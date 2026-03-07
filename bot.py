# Import de bibliothèques
import asyncio
import discord
import feedparser
from google import genai
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import sys

# Vérifie que le bot démarre correctement
print("Bot démarré", flush=True)
sys.stdout.flush()

# Récupération du token Discord et clé API dans le fichier ".env"
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configuration de Gemini en donnant la clé API et choisissant le modèle du LLM
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# Configuration Google Sheets : authentification et sélection de la feuille
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
sheets_client = gspread.authorize(creds)
spreadsheet = sheets_client.open_by_key("1OEq-tfr1vlHxrR5QJq1Z6NdYlweiDE1Ocjn5vqIuaXo")
sheet = spreadsheet.get_worksheet(0)

# Gestion des droits du bot Discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Flux RSS à surveiller
RSS_FEEDS = [
    "https://www.lemonde.fr/intelligence-artificielle/rss_full.xml",
]

# ID du canal Discord où poster les articles
CHANNEL_ID = 1479667999547064330

# Fichier qui stocke les liens des articles déjà postés pour éviter les doublons
POSTED_ARTICLES_FILE = "posted_articles.txt"

def load_posted_articles():
    # Retourne un set vide si le fichier n'existe pas encore
    if not os.path.exists(POSTED_ARTICLES_FILE):
        return set()
    # Lit le fichier et retourne les liens sous forme de set
    with open(POSTED_ARTICLES_FILE, "r") as f:
        return set(f.read().splitlines())

def save_posted_article(link):
    # Ajoute le lien de l'article dans le fichier pour ne plus le retraiter
    with open(POSTED_ARTICLES_FILE, "a") as f:
        f.write(link + "\n")

def get_summary(text):
    # Envoie le texte à Gemini et retourne un résumé de 3 lignes en français
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Résume cet article en 3 lignes en français : {text[:3000]}"
        )
        return response.text
    except Exception as e:
        # En cas d'erreur (quota dépassé, réseau...), on affiche l'erreur et on continue
        print(f"Erreur Gemini : {e}")
        return "Résumé indisponible pour le moment."

def export_to_sheets(title, link, summary, source):
    # Ajoute une nouvelle ligne dans le Google Sheets avec les infos de l'article
    try:
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        sheet.append_row([date, title, link, summary, source])
        print(f"Article exporté vers Google Sheets : {title}")
    except Exception as e:
        print(f"Erreur Google Sheets : {e}")

async def fetch_and_post():
    # Attend que le bot soit connecté à Discord avant de commencer
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    # Charge les articles déjà postés pour éviter les doublons
    posted_articles = load_posted_articles()

    for feed_url in RSS_FEEDS:
        # Parse le flux RSS et récupère les 3 derniers articles
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            # Si l'article a déjà été posté, on le skip
            if entry.link in posted_articles:
                print(f"Article déjà posté, skip : {entry.title}")
                continue
            # Génère le résumé et formate le message Discord
            summary = get_summary(entry.get("summary", entry.title))
            message = f"📰 **[{entry.title}]({entry.link})**\n\n{summary}\n\n🔗 Source: {feed.feed.title}"
            # Poste le message sur Discord et exporte vers Google Sheets
            await channel.send(message)
            export_to_sheets(entry.title, entry.link, summary, feed.feed.title)
            save_posted_article(entry.link)
            # Pause de 4 secondes pour respecter le quota de l'API Gemini
            await asyncio.sleep(4)

@client.event
async def on_ready():
    print(f"Bot connecté en tant que {client.user}")
    while True:
        # Calcule le temps restant jusqu'à 7h00 du matin
        now = datetime.now()
        target = now.replace(hour=7, minute=0, second=0, microsecond=0)
        # Si 7h00 est déjà passé aujourd'hui, on vise 7h00 demain
        if now >= target:
            target = target.replace(day=target.day + 1)
        wait_seconds = (target - now).total_seconds()
        print(f"Prochain lancement à 7h00, dans {int(wait_seconds/3600)}h{int((wait_seconds%3600)/60)}min")
        # Attend jusqu'à 7h00 puis lance la récupération des articles
        await asyncio.sleep(wait_seconds)
        await fetch_and_post()

# Lance le bot avec le token Discord
client.run(DISCORD_TOKEN)