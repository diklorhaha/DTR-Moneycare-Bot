# ticket-yoomoney-bot

Discord-бот для тикетов Ticket Tool + оплата через ЮMoney Quickpay.

## Что делает

1. Ждёт канал `ticket-*`
2. Читает из embed Ticket Tool поле **Сумма робуксов для покупки:**
3. Считает рубли: `робуксы / ROBUX_RATE`
4. Шлёт ссылку на оплату ЮMoney
5. Ждёт оплату (опрос истории + опционально webhook)
6. При успехе — сообщение покупателю; при таймауте — закрывает тикет

## Быстрый старт

```bash
cd ~/Projects/ticket-yoomoney-bot
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
```

### 1. Discord

1. [Discord Developer Portal](https://discord.com/developers/applications) → Bot → скопируй token в `DISCORD_BOT_TOKEN`
2. Включи privileged intent **Message Content Intent**
3. Invite с правами: View Channels, Send Messages, Read Message History, Manage Channels (для удаления тикета)
4. Бот должен видеть те же ticket-каналы, что и Ticket Tool (роль/категория)

### 2. ЮMoney

1. `YOOMONEY_WALLET` — номер кошелька-получателя
2. Получи `YOOMONEY_ACCESS_TOKEN` (права `operation-history`):

```bash
python scripts/get_yoomoney_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_SECRET --redirect-uri https://localhost
```

Вставь токен в `.env`. `redirect_uri` должен совпадать с тем, что в настройках приложения ЮMoney.

3. Курс: `ROBUX_RATE=2` → `2000 / 2 = 1000 ₽`

### 3. Запуск

```bash
python -m bot.main
```

## Опционально: мгновенные уведомления

В настройках кошелька ЮMoney включи HTTP-уведомления на:

`https://YOUR_PUBLIC_HOST:8080/yoomoney/notification`

В `.env`:

```
YOOMONEY_WEBHOOK_ENABLED=true
YOOMONEY_NOTIFICATION_SECRET=секрет_из_кабинета
YOOMONEY_WEBHOOK_PORT=8080
```

Без webhook бот всё равно работает — поллит `operation-history`.

## Настройка текстов

Правь `MSG_*` в `.env` или `bot/messages.py`. Плейсхолдеры: `{robux}`, `{rub}`, `{payment_url}`, `{minutes}`.

## Тесты

```bash
pytest
ruff check .
```
