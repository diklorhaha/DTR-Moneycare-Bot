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

## Деплой на Amvera

1. В корне уже есть `amvera.yml` (Python 3.11, старт: `python -m bot.main`).
2. Секреты **не** клади в git — добавь их в Amvera → **Переменные** (как в `.env.example`):
   - `DISCORD_BOT_TOKEN`
   - `YOOMONEY_WALLET`
   - `YOOMONEY_ACCESS_TOKEN`
   - `ROBUX_RATE`
   - остальное по желанию
3. Залей код в git Amvera (из скрина):

```bash
cd C:\Users\Бебрик\Projects\ticket-yoomoney-bot
git add .
git commit -m "feat: ticket yoomoney discord bot"
git remote add amvera https://git.msk0.amvera.ru/dtrshop/dtr-moneycare
git push -u amvera master
```

Логин/пароль или токен — те, что даёт Amvera для своего git. После push проект соберётся и запустит бота.

Webhook ЮMoney на Amvera нужен только если включишь `YOOMONEY_WEBHOOK_ENABLED=true` (тогда понадобится публичный URL и порт в настройках приложения). По умолчанию хватает поллинга оплаты — webhook не обязателен.
