# =========================
# Imports
# =========================
import asyncio
import discord
import feedparser
from google import genai
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import sys

# =========================
# Démarrage
# =========================
print("Bot démarré", flush=True)
sys.stdout.flush()

BOT_START_TIME = datetime.now()
LAST_RUN = None

# =========================
# Variables d'environnement
# =========================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# Gemini (résumés IA)
# =========================
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# =========================
# Google Sheets
# =========================
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)
sheets_client = gspread.authorize(creds)
spreadsheet = sheets_client.open_by_key(
    "1OEq-tfr1vlHxrR5QJq1Z6NdYlweiDE1Ocjn5vqIuaXo"
)
sheet = spreadsheet.get_worksheet(0)

# =========================
# Discord
# =========================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

CHANNEL_ID = 1479667999547064330

# =========================
# Flux RSS par jour
# =========================
RSS_FEEDS = {
    0: ("Le Monde IA", "https://www.lemonde.fr/intelligence-artificielle/rss_full.xml"),
    1: ("Numerama IA", "https://www.numerama.com/tag/intelligence-artificielle/feed/"),
    2: ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
    3: ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    4: ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    5: ("Le Monde IA", "https://www.lemonde.fr/intelligence-artificielle/rss_full.xml"),
    6: ("Numerama IA", "https://www.numerama.com/tag/intelligence-artificielle/feed/"),
}

# =========================
# Articles déjà postés
# =========================
POSTED_ARTICLES_FILE = "posted_articles.txt"

def load_posted_articles():
    if not os.path.exists(POSTED_ARTICLES_FILE):
        return set()
    with open(POSTED_ARTICLES_FILE, "r") as f:
        return set(f.read().splitlines())

def save_posted_article(link):
    with open(POSTED_ARTICLES_FILE, "a") as f:
        f.write(link + "\n")

# =========================
# Résumé IA
# =========================
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

# =========================
# Export Google Sheets
# =========================
def export_to_sheets(title, link, summary, source):
    try:
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        sheet.append_row([date, title, link, summary, source])
        print(f"Article exporté vers Google Sheets : {title}")
    except Exception as e:
        print(f"Erreur Google Sheets : {e}")

# =========================
# Fetch & Post
# =========================
async def fetch_and_post():
    global LAST_RUN
    LAST_RUN = datetime.now()

    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    posted_articles = load_posted_articles()

    day = datetime.now().weekday()
    source_name, feed_url = RSS_FEEDS[day]
    print(f"Source du jour ({day}) : {source_name}")

    feed = feedparser.parse(feed_url)

    for entry in feed.entries[:3]:
        if entry.link in posted_articles:
            print(f"Article déjà posté, skip : {entry.title}")
            continue

        posted_articles.add(entry.link)

        summary = get_summary(entry.get("summary", entry.title))
        message = (
            f"📰 **[{entry.title}]({entry.link})**\n\n"
            f"{summary}\n\n"
            f"🔗 Source : {source_name}"
        )

        await channel.send(message)
        export_to_sheets(entry.title, entry.link, summary, source_name)
        save_posted_article(entry.link)

        await asyncio.sleep(15)

# =========================
# Scheduler quotidien
# =========================
async def daily_scheduler():
    await client.wait_until_ready()

    while not client.is_closed():
        now = datetime.now()
        target = now.replace(hour=7, minute=0, second=0, microsecond=0)

        if now >= target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()

        print(
            f"Prochain lancement à 7h00, dans "
            f"{int(wait_seconds // 3600)}h"
            f"{int((wait_seconds % 3600) // 60)}min"
        )

        await asyncio.sleep(wait_seconds)
        await fetch_and_post()

# =========================
# on_ready (une seule fois)
# =========================
scheduler_started = False

@client.event
async def on_ready():
    global scheduler_started
    print(f"Bot connecté en tant que {client.user}")

    if not scheduler_started:
        scheduler_started = True
        client.loop.create_task(daily_scheduler())

# =========================
# Commande !status
# =========================
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "!status":
        now = datetime.now()
        uptime = now - BOT_START_TIME

        next_run = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)

        day = now.weekday()
        source_name, _ = RSS_FEEDS[day]
        posted_count = len(load_posted_articles())

        status_message = (
            "**📊 Statut du bot Veille Tech**\n\n"
            "🟢 En ligne\n"
            f"⏱️ Uptime : {uptime.days}j {uptime.seconds // 3600}h\n"
            f"🕖 Prochain lancement : {next_run.strftime('%d/%m à %H:%M')}\n"
            f"📰 Source du jour : {source_name}\n"
            f"📦 Articles déjà postés : {posted_count}\n"
            f"🕰️ Dernier run : "
            f"{LAST_RUN.strftime('%d/%m %H:%M') if LAST_RUN else 'Pas encore exécuté'}"
        )

        await message.channel.send(status_message)

# =========================
# Lancement
# =========================
client.run(DISCORD_TOKEN)