import os
import logging
import asyncio
from dotenv import load_dotenv
import requests
import json

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Налаштування логування для кращого дебагу
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Завантажуємо змінні оточення з .env файлу
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Назви файлів для зберігання даних
SENT_ANNOUNCEMENTS_FILE = 'sent_announcements.json'
CHAT_IDS_FILE = 'chat_ids.json'


# --- Функції для роботи з файлами ---

def load_json_file(filename: str) -> set:
    """Завантажує дані з JSON-файлу і повертає їх як множину (set)."""
    try:
        with open(filename, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_json_file(filename: str, data: set):
    """Зберігає множину (set) у JSON-файл."""
    with open(filename, 'w') as f:
        json.dump(list(data), f, indent=4)


# --- Логіка роботи з Bybit API ---

def fetch_bybit_announcements() -> list:
    """Отримує останні анонси з Bybit API."""
    url = "https://api.bybit.com/v5/announcements/index"
    params = {
        "locale": "en-US",  # Використовуємо англійську для надійного пошуку "splash"
        "limit": 20  # Кількість останніх анонсів для перевірки
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Перевіряє наявність HTTP-помилок
        data = response.json()
        if data.get("retCode") == 0 and data.get("result"):
            return data["result"]["list"]
        else:
            logger.error(f"Помилка в API відповіді від Bybit: {data.get('retMsg')}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка під час запиту до Bybit API: {e}")
        return []


# --- Функції та команди Telegram-бота ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /start.
    Зберігає chat_id для майбутніх розсилок.
    """
    chat_id = update.message.chat_id
    chat_ids = load_json_file(CHAT_IDS_FILE)

    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        save_json_file(CHAT_IDS_FILE, chat_ids)
        await update.message.reply_text(
            "Привіт! Цей чат додано до списку розсилки.\n"
            "Я буду повідомляти вас про нові Token Splash на Bybit."
        )
        logger.info(f"Новий чат додано до розсилки: {chat_id}")
    else:
        await update.message.reply_text("Цей чат вже є у списку розсилки.")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /test.
    Шукає останній анонс про Token Splash і надсилає його в чат.
    """
    await update.message.reply_text("🔎 Шукаю останній анонс Token Splash...")

    announcements = fetch_bybit_announcements()
    if not announcements:
        await update.message.reply_text("Не вдалося отримати анонси з Bybit. Спробуйте пізніше.")
        return

    found_splash = None
    # API повертає найновіші першими, тому шукаємо перше ж співпадіння
    for ann in announcements:
        title = ann.get('title', '').lower()
        if "splash" in title:
            found_splash = ann
            break  # Знайшли найновіший, виходимо з циклу

    if found_splash:
        message = (
            f"✅ <b>Ось останній знайдений Token Splash (тестове повідомлення):</b>\n\n"
            f"<b>Заголовок:</b> {found_splash.get('title')}\n\n"
            f"<b>Дата публікації:</b> {found_splash.get('created_at')}\n\n"
            f"👇 <b>Посилання на анонс:</b>\n{found_splash.get('url')}"
        )
        await update.message.reply_text(
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text("😕 Не вдалося знайти жодного анонсу про Token Splash серед останніх 20 новин.")


async def check_announcements(context: ContextTypes.DEFAULT_TYPE):
    """
    Основна функція, яка перевіряє анонси і розсилає повідомлення.
    Виконується періодично завдяки JobQueue.
    """
    bot: Bot = context.bot
    logger.info("Перевірка нових анонсів Bybit...")

    announcements = fetch_bybit_announcements()
    if not announcements:
        return

    sent_ids = load_json_file(SENT_ANNOUNCEMENTS_FILE)
    chat_ids = load_json_file(CHAT_IDS_FILE)

    if not chat_ids:
        logger.warning("Немає зареєстрованих чатів для відправки повідомлень.")
        return

    for ann in reversed(announcements):  # Перевіряємо від старіших до новіших
        ann_id = ann.get('id')
        title = ann.get('title', '').lower()
        url = ann.get('url')

        # Перевіряємо, чи це новий анонс і чи є в ньому слово "splash"
        if ann_id and str(ann_id) not in sent_ids and "splash" in title:
            logger.info(f"Знайдено новий Token Splash: {ann.get('title')}")

            # Формуємо повідомлення
            message = (
                f"🔥 <b>Новий Token Splash на Bybit!</b> 🔥\n\n"
                f"<b>Заголовок:</b> {ann.get('title')}\n\n"
                f"<b>Дата публікації:</b> {ann.get('created_at')}\n\n"
                f"👇 <b>Посилання на анонс:</b>\n{url}"
            )

            # Розсилаємо повідомлення у всі збережені чати
            for chat_id in list(chat_ids):  # Копіюємо, щоб можна було видаляти елементи
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    await asyncio.sleep(0.1)  # Невеликий таймаут, щоб не спамити API Telegram
                except Exception as e:
                    # Якщо бот був заблокований або видалений з чату
                    logger.error(f"Не вдалося надіслати повідомлення в чат {chat_id}: {e}")
                    if "bot was kicked" in str(e) or "chat not found" in str(e):
                        logger.info(f"Видалення чату {chat_id} зі списку розсилки.")
                        chat_ids.remove(chat_id)
                        save_json_file(CHAT_IDS_FILE, chat_ids)

            # Додаємо ID анонсу до списку відправлених і зберігаємо
            sent_ids.add(str(ann_id))
            save_json_file(SENT_ANNOUNCEMENTS_FILE, sent_ids)


def main():
    """Основна функція запуску бота."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("Не знайдено TELEGRAM_BOT_TOKEN! Перевірте ваш .env файл.")
        return

    # Створюємо додаток
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Додаємо обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test))

    # Створюємо та запускаємо періодичне завдання для перевірки анонсів
    job_queue = application.job_queue
    # Перевіряти кожні 5 хвилин (300 секунд)
    job_queue.run_repeating(check_announcements, interval=300, first=10)

    logger.info("Бот запущений і готовий до роботи!")

    # Запускаємо бота
    application.run_polling()


if __name__ == '__main__':
    main()
