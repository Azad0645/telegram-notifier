import time
import requests
import telegram
import os
import logging
from dotenv import load_dotenv


class TelegramLogsHandler(logging.Handler):

    def __init__(self, bot: telegram.Bot, chat_id: str):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = self.format(record)
            log_entry = log_entry[:4000]
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception:
            pass


logger = logging.getLogger("telegram_notifier")


def main():
    load_dotenv()

    tg_token = os.environ["TG_TOKEN"]
    dvmn_token = os.environ["DVMN_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    bot = telegram.Bot(token=tg_token)
    dvmn_url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {dvmn_token}"}

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    tg_handler = TelegramLogsHandler(bot, chat_id)
    tg_handler.setLevel(logging.INFO)
    tg_handler.setFormatter(formatter)
    logger.addHandler(tg_handler)

    logger.info("Бот запущен, жду проверок от dvmn.org...")

    timestamp: str | None = None

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
                logger.debug("Таймаут, новый timestamp: %s", timestamp)

            elif review_data["status"] == "found":
                logger.info("Найдены новые проверки (%s шт.)", len(review_data["new_attempts"]))

                for attempt in review_data["new_attempts"]:
                    title = attempt.get("lesson_title", "Без названия")
                    negative = attempt.get("is_negative", True)

                    logger.info(
                        "Проверена работа: %s, результат: %s",
                        title,
                        "нужны правки" if negative else "принята",
                    )

                    bot.send_message(chat_id=chat_id, text=f"Преподаватель проверил работу!:\n{title}")

                    if negative:
                        bot.send_message(chat_id=chat_id, text="Нужны правки")
                    else:
                        bot.send_message(chat_id=chat_id, text="Работа принята")

                timestamp = review_data["last_attempt_timestamp"]

        except requests.exceptions.ReadTimeout:
            continue

        except requests.exceptions.ConnectionError:
            logger.warning("Проблемы с подключением. Повтор через 5 секунд...")
            time.sleep(5)

        except Exception:
            logger.exception("Неожиданная ошибка в цикле long polling")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Остановлено по Ctrl+C")
    except Exception:
        logger.exception("Критическая ошибка в main()")
        raise