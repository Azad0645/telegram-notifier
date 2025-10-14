import time
import requests
import telegram
import os
from dotenv import load_dotenv


def main():
    load_dotenv()

    tg_token = os.environ["TG_TOKEN"]
    dvmn_token = os.environ["DVMN_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    bot = telegram.Bot(token=tg_token)
    dvmn_url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {dvmn_token}"}

    timestamp = None

    while True:
        params = {}
        if timestamp:
            params["timestamp"] = timestamp

        try:
            response = requests.get(dvmn_url, headers=headers, params=params, timeout=100)
            response.raise_for_status()
            review_data = response.json()

            if review_data["status"] == "timeout":
                timestamp = review_data["timestamp_to_request"]

            elif review_data["status"] == "found":
                for attempt in review_data["new_attempts"]:
                    title = attempt.get("lesson_title", "Без названия")
                    negative = attempt.get("is_negative", True)

                    bot.send_message(chat_id=chat_id, text=f"Преподаватель проверил работу!:\n{title}")

                    if negative:
                        bot.send_message(chat_id=chat_id, text="Нужны правки")
                    else:
                        bot.send_message(chat_id=chat_id, text="Работа принята")

                timestamp = review_data["last_attempt_timestamp"]

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            print("Проблемы с подключением. Повтор через 5 секунд...")
            time.sleep(5)


if __name__ == "__main__":
    main()