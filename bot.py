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

# Flux RSS organisés par jour de la semaine (0=Lundi, 6=Dimanche)
RSS_FEEDS = {
    0: ("Le Monde IA", "https://www.lemonde.fr/intelligence-artificielle/rss_full.xml"),
    1: ("Numerama IA", "https://www.numerama.com/tag/intelligence-artificielle/feed/"),
    2: ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
    3: ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    4: ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    5: ("Le Monde IA", "https://www.lemonde.fr/intelligence-artificielle/rss_full.xml"),
    6: ("Numerama IA", "https://www.numerama.com/tag/intelligence-artificielle/feed/"),
}

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
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    # Charge les articles déjà postés
    posted_articles = load_posted_articles()

    # Sélectionne la source du jour
    day = datetime.now().weekday()
    source_name, feed_url = RSS_FEEDS[day]
    print(f"Source du jour ({day}) : {source_name}")

    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:3]:
        if entry.link in posted_articles:
            print(f"Article déjà posté, skip : {entry.title}")
            continue
        # Ajoute immédiatement au set en mémoire pour éviter les doublons
        posted_articles.add(entry.link)
        summary = get_summary(entry.get("summary", entry.title))
        message = f"📰 **[{entry.title}]({entry.link})**\n\n{summary}\n\n🔗 Source: {source_name}"
        await channel.send(message)
        export_to_sheets(entry.title, entry.link, summary, source_name)
        save_posted_article(entry.link)
        await asyncio.sleep(15)

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
