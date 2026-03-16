# 🤖 Veille Tech Bot

> Bot Discord de veille automatique sur l'intelligence artificielle — Projet BTS SIO 2026

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.x-5865F2?logo=discord)](https://discordpy.readthedocs.io)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange?logo=google)](https://ai.google.dev)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-Server%2024.04-E95420?logo=ubuntu)](https://ubuntu.com)

---

## 📋 Présentation

**Veille Tech Bot** automatise entièrement le processus de veille informatique sur l'IA. Chaque matin à **7h00**, le bot récupère les derniers articles depuis un flux RSS, les résume grâce à l'API Google Gemini, les poste dans un canal Discord et les exporte dans un Google Sheets.

### Avant / Après

| Avant | Après |
|-------|-------|
| Consultation manuelle de Feedly | Récupération automatique via RSS |
| Résumé manuel via ChatGPT | Résumé automatique via Google Gemini |
| Saisie manuelle dans un tableur | Export automatique vers Google Sheets |

---

## ✨ Fonctionnalités

- 📰 **Collecte automatique** des articles via flux RSS
- 🧠 **Résumé en 3 lignes** généré par Google Gemini 2.5 Flash
- 💬 **Publication Discord** avec titre cliquable, résumé et source
- 📊 **Export Google Sheets** automatique (date, titre, lien, résumé, source)
- 🔁 **Anti-doublons** : les articles déjà traités sont ignorés
- 📅 **Une source par jour** pour optimiser le quota de l'API Gemini
- ⚙️ **Service systemd** : redémarre automatiquement au reboot du serveur

---

## 🗓️ Planification des sources

| Jour | Source |
|------|--------|
| Lundi | Le Monde IA |
| Mardi | Numerama IA |
| Mercredi | The Verge AI |
| Jeudi | VentureBeat AI |
| Vendredi | TechCrunch AI |
| Samedi | Le Monde IA |
| Dimanche | Numerama IA |

---

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Serveur | Ubuntu Server 24.04 |
| Langage | Python 3.12 |
| Bot Discord | discord.py |
| Flux RSS | feedparser |
| IA | Google Gemini 2.5 Flash |
| Export | gspread + Google Sheets API |
| Planification | asyncio + systemd |

---

## 🚀 Installation

### Prérequis

- Un serveur Linux (Ubuntu Server recommandé)
- Un compte Discord avec un bot créé sur le [portail développeur](https://discord.com/developers/applications)
- Une clé API [Google Gemini](https://aistudio.google.com)
- Un compte Google avec accès à l'API Google Sheets

### 1. Cloner le projet

```bash
git clone https://github.com/whizpixel/veille.git
cd veille
```

### 2. Créer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install discord.py feedparser google-genai gspread google-auth python-dotenv
```

### 4. Configurer les variables d'environnement

Crée un fichier `.env` à la racine du projet :

```env
DISCORD_TOKEN=ton_token_discord
GEMINI_API_KEY=ta_clé_gemini
```

### 5. Ajouter les credentials Google Sheets

Place le fichier JSON du compte de service Google dans le dossier du projet :

```
credentials.json
```

### 6. Configurer le bot

Dans `bot.py`, modifie les variables suivantes :

```python
CHANNEL_ID = TON_ID_DE_CANAL_DISCORD
spreadsheet = sheets_client.open_by_key("TON_ID_GOOGLE_SHEETS")
```

### 7. Lancer le bot

```bash
python3 bot.py
```

---

## ⚙️ Configuration comme service systemd

Pour que le bot tourne en permanence et redémarre automatiquement :

```bash
sudo nano /etc/systemd/system/discord-bot.service
```

```ini
[Unit]
Description=Discord Veille Tech Bot
After=network.target

[Service]
Type=simple
User=TON_UTILISATEUR
WorkingDirectory=/chemin/vers/veille
ExecStart=/chemin/vers/veille/venv/bin/python3 /chemin/vers/veille/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

---

## 📖 Commandes utiles

```bash
sudo systemctl status discord-bot    # État du bot
sudo systemctl restart discord-bot  # Redémarrer
sudo systemctl stop discord-bot     # Arrêter
sudo journalctl -u discord-bot -f   # Logs en temps réel
```

---

## 📁 Structure du projet

```
veille/
├── bot.py                  # Code principal du bot
├── credentials.json        # Credentials Google (non versionné)
├── .env                    # Variables d'environnement (non versionné)
├── posted_articles.txt     # Liens des articles déjà postés (non versionné)
├── index.html              # Site de documentation
└── README.md               # Ce fichier
```

---

## ⚠️ Sécurité

Les fichiers suivants sont ignorés par Git via `.gitignore` :

- `.env` — contient les tokens et clés API
- `credentials.json` — contient la clé privée Google
- `posted_articles.txt` — données locales

Ne partagez jamais ces fichiers publiquement.

---

## 📚 Documentation

La documentation complète est disponible sur : **[whizpixel.github.io/veille](https://whizpixel.github.io/veille)**

---

## 👤 Auteur

**Yunus** — Projet de fin de BTS SIO 2026
