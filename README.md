# Bybit Token Splash Telegram Bot

A Telegram bot that monitors [Bybit](https://www.bybit.com)'s announcement feed for new Token Splash events and notifies subscribed users in real-time.

## Features

- ✅ Automatically fetches the latest announcements from Bybit API.
- 🔍 Detects and identifies announcements containing "Token Splash".
- 💬 Sends updates to all subscribed chats using Telegram.
- 🧠 Persists sent announcement IDs and chat IDs to prevent duplicates.
- 📅 Periodically checks for new announcements (every 5 minutes).
- 🔧 Provides commands for users to subscribe and test the functionality.

## Requirements

- Python 3.9+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- `.env` file containing your bot token

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/bybit-token-splash-bot.git
   cd bybit-token-splash-bot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file**

   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. **Run the bot**

   ```bash
   python bot.py
   ```

## Commands

- `/start` – Registers the chat to receive notifications.
- `/test` – Manually checks the latest 20 announcements and sends the newest Token Splash (if any) to the chat.

## Files

- `sent_announcements.json` – Stores the IDs of announcements already sent to avoid duplicates.
- `chat_ids.json` – Stores Telegram chat IDs that subscribed via `/start`.

## Scheduled Jobs

The bot checks Bybit's announcements every **5 minutes** and sends messages to all subscribed chats if a new Token Splash is found.

## Logging

Uses Python's built-in logging module to print detailed logs to the console, including errors, API issues, and chat registration.



> Developed with ❤️ by Zyabi