# Telegram Notifier

Бот, который уведомляет в Telegram, когда преподаватель проверил твою работу на [dvmn.org](https://dvmn.org).

## Запуск

Установите зависимости:

- `pip install -r requirements.txt`

Создайте файл .env и добавьте туда свои токены:

- TG_TOKEN=токен_бота
- DVMN_TOKEN=токен_dvmn.org

Запуск бота:

- `python main.py --chat_id 123456789`
