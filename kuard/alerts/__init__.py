from .telegram import alert_telegram
#, start_bot, load_env_variables
import os
import configparser
"""
def notify(message: str):
    alert_telegram(message)
"""
#if os.path.exists("env_config.ini"):
 #  load_env_variables('env_config.ini')

def notify(message: str):
   # if not "telegram_chat_id" in os.environ:
     #   start_bot()
    alert_telegram(message)




