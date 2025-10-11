import time
import requests
import telegram
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
DVMN_TOKEN = os.getenv("DVMN_TOKEN")

parser = argparse.ArgumentParser(description="DVMN Telegram notifier")
parser.add_argument("--chat_id", required=True, help="Ваш chat_id в Telegram")
args = parser.parse_args()
CHAT_ID = args.chat_id

bot = telegram.Bot(token=TG_TOKEN)
DVMN_URL = "https://dvmn.org/api/long_polling/"
headers = {"Authorization": f"Token {DVMN_TOKEN}"}

timestamp = None

while True:
    params = {}
    if timestamp:
        params["timestamp"] = timestamp

    try:
        response = requests.get(DVMN_URL, headers=headers, params=params, timeout=100)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "timeout":
            timestamp = data["timestamp_to_request"]

        elif data["status"] == "found":
            for attempt in data["new_attempts"]:
                title = attempt.get("lesson_title", "Без названия")
                negative = attempt.get("is_negative", True)

                bot.send_message(chat_id=CHAT_ID, text=f"Преподаватель проверил работу!:\n{title}")

                if negative:
                    bot.send_message(chat_id=CHAT_ID, text="Нужны правки")
                else:
                    bot.send_message(chat_id=CHAT_ID, text="Работа принята")

            timestamp = data["last_attempt_timestamp"]

    except requests.exceptions.ReadTimeout:
        continue
    except requests.exceptions.ConnectionError:
        print("Проблемы с подключением. Повтор через 5 секунд...")
        time.sleep(5)