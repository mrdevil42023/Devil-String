# Devil String Bot — Telegram Session String Generator

A Telegram bot that generates Pyrogram (V1, V2, Bot) and Telethon (User, Bot) session strings.

---

## Features

- Generate **Pyrogram V1**, **Pyrogram V2**, and **Pyrogram Bot** session strings
- Generate **Telethon** and **Telethon Bot** session strings
- Admin commands: `/stats`, `/broadcast`, `/users`
- User data stored in OpenSearch

---

## Environment Variables

Set these in your hosting platform (fps.ms Variables tab):

| Variable | Description |
|---|---|
| `API_ID` | Your Telegram API ID from my.telegram.org |
| `API_HASH` | Your Telegram API Hash from my.telegram.org |
| `BOT_TOKEN` | Your bot token from @BotFather |
| `OWNER_ID` | Your Telegram numeric user ID |
| `OPENSEARCH_URI` | OpenSearch connection URI (e.g. https://user:pass@host:24832) |

---

## Deploy on fps.ms

### Step 1 — Create an account
Go to https://fps.ms and sign up or log in.

### Step 2 — Create a new project
Click New Project and choose Upload ZIP.

### Step 3 — Upload this ZIP
Upload the Devil-String-Bot-fpsms.zip file you downloaded.

### Step 4 — Set environment variables
Go to your project Variables tab and add all the variables from the table above.

### Step 5 — Set the start command
Make sure the start command is: python main.py
fps.ms will auto-detect this from the Procfile.

### Step 6 — Deploy
Click Deploy. Watch the logs — you should see:
Bot @yourbotusername is now ready to generate sessions.

---

## How to Get Your Credentials

- API_ID / API_HASH: Go to https://my.telegram.org, log in, go to API Development Tools, create a new app
- BOT_TOKEN: Message @BotFather on Telegram, send /newbot
- OWNER_ID: Message @userinfobot on Telegram to get your numeric user ID
- OPENSEARCH_URI: Sign up at https://bonsai.io for a free OpenSearch cluster

---

## Using the Bot

1. Start the bot with /start
2. Click Generate Session
3. Choose session type (Pyrogram V1, V2, Bot, or Telethon)
4. Follow the prompts (enter API ID, API Hash, phone number, OTP)
5. Receive your session string

---

## Admin Commands

| Command | Description |
|---|---|
| /stats | Show total user count |
| /broadcast message | Send a message to all users |
| /users | List all registered users |
