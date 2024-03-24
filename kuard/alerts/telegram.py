import os
from dotenv import load_dotenv
import sys
import subprocess

load_dotenv('.env')
tel_tok = os.getenv("TELEGRAM_TOKEN")
if tel_tok is None:
     os.environ["TELEGRAM_TOKEN"] = "7034741381:AAGfECxVwQSId3tXlJCm4dBWoUSjI1_sc7o"



def alert_telegram(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_ID")
    if token and chat_id:
        #bot.send_message(chat_id=chat_id, text=message)
       message = message.replace(" ", "%20")
       curl_command = f"curl 'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}'"
       subprocess.run(curl_command, shell=True)

