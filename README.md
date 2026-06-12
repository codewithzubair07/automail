<<<<<<< HEAD
# AI Email Automation System (Flask + Groq + Gmail + Telegram)

A fully Python-based, free AI email automation app.

## Features

- Business onboarding chat assistant using Groq (`llama-3.3-70b-versatile`)
- Business knowledge extraction and storage in `data.json`
- Gmail OAuth connection and unread email scanning
- AI-generated auto-replies based on your business profile
- Telegram notifications for each processed enquiry
- Real-time monitor activity feed via Flask-SocketIO
- Full reply logs with original email and sent reply text

## Tech Stack

- Flask + Flask-SocketIO
- Groq Python SDK
- Gmail API (`google-api-python-client`, OAuth)
- Telegram Bot API (`requests`)
- Local JSON storage (`data.json`)

## Setup

1. Clone / open this project folder.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example`:

```env
GROQ_API_KEY=your_groq_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

5. Put your Google OAuth desktop client file as `credentials.json` in project root.
6. Run app:

```bash
python app.py
```

7. Open:

```text
http://localhost:5000
```

## First-Time Flow

1. Use **Business Setup** tab to chat with the agent and provide business details.
2. Click **Save Business Knowledge**.
3. Use **Settings** tab to connect Gmail and configure Telegram.
4. Save settings and optionally test Telegram.
5. Start monitoring from **Monitor** tab.

## Important Notes

- `token.json` is created after Gmail OAuth and should not be committed.
- `data.json` is auto-created on first run.
- Monitoring thread runs as daemon and stops with app shutdown.
=======
# automail
>>>>>>> ae61376243290dc7d5c929cc76cbd3cbce9c4736
