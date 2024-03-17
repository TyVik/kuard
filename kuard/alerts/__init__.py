from telegram import alert_telegram


def notify(message: str):
    alert_telegram(message)
