from .telegram import alert_telegram
import os
import configparser


def notify(message: str):
    alert_telegram(message)




