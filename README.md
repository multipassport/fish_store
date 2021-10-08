# fish_store

Рыбная витрина в телеграм боте. Подключена к API [ElasticPath](https://www.elasticpath.com)

## Установка

Для запуска программы должен быть установлен Python 3.

Скачайте код и установите требуемые библиотеки командой

```bash
pip install -r requirements.txt

```

## Переменные окружения

Для запуска ботов понадобится `.env` файл следующего содержимого:

* `STORE_ID` - Store ID из дэшборда [ElasticPath](https://dashboard.elasticpath.com/app)
* `CLIENT_ID` - Client ID из дэшборда [ElasticPath](https://dashboard.elasticpath.com/app)
* `CLIENT_SECRET` - Client Secret из дэшборда [ElasticPath](https://dashboard.elasticpath.com/app)
* `TG_BOT_TOKEN` - токен Telegram бота. Получается у [@BotFather](https://telegram.me/BotFather)
* `REDIS_ENDPOINT` - адрес базы данных [redis](https://app.redislabs.com/)
* `REDIS_PORT` - номер порта базы данных [redis](https://app.redislabs.com/)
* `REDIS_PASSWORD` - пароль от базы данных [redis](https://app.redislabs.com/)
* `TG_CHAT_ID` - ID чата Telegram, куда должны приходить сообщения логгера
* `TG_LOG_BOT_TOKEN` - токен запасного Telegram бота. Получается у [@BotFather](https://telegram.me/BotFather)

## Запуск ботов

Бот запускается командой 

```bash
python bot.py

```

## Предварительный просмотр

Бот доступен для просмотра [здесь](@mltfishbot)

## Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).
