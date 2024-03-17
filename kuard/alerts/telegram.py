import os

import telebot


def alert_telegram(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if token and chat_id:
        bot = telebot.TeleBot(token=token)
        bot.send_message(chat_id=chat_id, text=message)
