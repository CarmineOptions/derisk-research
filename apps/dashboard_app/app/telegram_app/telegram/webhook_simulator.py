import os
import time
import requests
import logging
from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
X_TELEGRAM_BOT_API_SECRET_TOKEN = os.getenv("X_TELEGRAM_BOT_API_SECRET_TOKEN")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
webhook_endpoint = "http://backend:8000/api/telegram/webhook"
allowed_updates = ["message", "poll_answer", "callback_query"]
timeout = 1
offset = 0



def get_updates():   
    global offset
    updates = f"&allowed_updates={','.join(allowed_updates)}" if allowed_updates else ""
    url = f"{API_URL}/getUpdates?offset={offset}{updates}"

    response = requests.get(url)
    data = response.json()

    if data["ok"]:
        for update in data["result"]:
            print("#Update ID", update["update_id"])
            offset = update["update_id"] + 1

            attempts = 5
            while attempts > 0:              
                result = requests.post(
                    webhook_endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "X-Telegram-Bot-Api-Secret-Token": X_TELEGRAM_BOT_API_SECRET_TOKEN,
                    },
                    json=update,
                )

                if 200 <= result.status_code < 300:
                    break
                attempts -= 1
    else:
        print("Error", data)


requests.get(f"{API_URL}/deleteWebhook")
while True:
    get_updates()
    time.sleep(timeout)
