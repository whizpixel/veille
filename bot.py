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
print("Bot démarré", flush=True)
sys.stdout.flush()

# Récupération du token Discord et clé api dans le fichier ".env"
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configuration de Gemini en donnant la clé API et choisissant le modèle du LLM
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# Configuration Google Sheets
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
sheets_client = gspread.authorize(creds)
spreadsheet = sheets_client.open_by_key("1OEq-tfr1vlHxrR5QJq1Z6NdYlweiDE1Ocjn5vqIuaXo")
sheet = spreadsheet.get_worksheet(0)

# Gestion des droits du bot
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Flux RSS à surveiller
RSS_FEEDS = [
    "https://www.lemonde.fr/intelligence-artificielle/rss_full.xml",
]

# ID du canal Discord où poster les articles
CHANNEL_ID = 1479667999547064330

#Évite les doublons
POSTED_ARTICLES_FILE = "posted_articles.txt"

def load_posted_articles():
    if not os.path.exists(POSTED_ARTICLES_FILE):
        return set()
    with open(POSTED_ARTICLES_FILE, "r") as f:
        return set(f.read().splitlines())

def save_posted_article(link):
    with open(POSTED_ARTICLES_FILE, "a") as f:
        f.write(link + "\n")

# Fonction qui génère le résumé de Gemini
def get_summary(text):
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Résume cet article en 3 lignes en français : {text[:3000]}"
        )
        return response.text
    except Exception as e:
        print(f"Erreur Gemini : {e}")
        return "Résumé indisponible pour le moment."
    
def export_to_sheets(title, link, summary, source):
    try:
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        sheet.append_row([date, title, link, summary, source])
        print(f"Article exporté vers Google Sheets : {title}")
    except Exception as e:
        print(f"Erreur Google Sheets : {e}")

async def fetch_and_post():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    
    posted_articles = load_posted_articles()

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:
            if entry.link in posted_articles:
                print(f"Article déjà posté, skip : {entry.title}")
                continue
            summary = get_summary(entry.get("summary", entry.title))
            message = f"📰 **[{entry.title}]({entry.link})**\n\n{summary}\n\n🔗 Source: {feed.feed.title}"
            await channel.send(message)
            export_to_sheets(entry.title, entry.link, summary, feed.feed.title)
            save_posted_article(entry.link)
            await asyncio.sleep(4)

@client.event
async def on_ready():
    print(f"Bot connecté en tant que {client.user}")
    while True:
        now = datetime.now()
        target = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target.replace(day=target.day + 1)
        wait_seconds = (target - now).total_seconds()
        print(f"Prochain lancement à 7h00, dans {int(wait_seconds/3600)}h{int((wait_seconds%3600)/60)}min")
        await asyncio.sleep(wait_seconds)
        await fetch_and_post()  

client.run(DISCORD_TOKEN)