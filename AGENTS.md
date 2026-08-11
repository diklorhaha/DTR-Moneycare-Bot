# ticket-yoomoney-bot

> Discord-бот: тикеты Ticket Tool → расчёт суммы → ссылка ЮMoney → ожидание оплаты / таймаут.

## Overview

Бот слушает создание каналов `ticket-*`, читает из embed Ticket Tool поле «Сумма робуксов для покупки:», считает сумму в рублях по курсу, выдаёт Quickpay-ссылку ЮMoney и либо подтверждает оплату, либо закрывает тикет по таймауту.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Framework | discord.py 2.x |
| Payments | YooMoney Quickpay + Wallet API (`operation-history`) |
| HTTP (optional webhook) | aiohttp |
| Config | python-dotenv |
| Testing | pytest |
| Lint | ruff |

## Quick Start

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # затем заполни значения

python -m bot.main

# tests
pytest

# lint
ruff check .
```

## Project Structure

```
bot/
  main.py              # entrypoint, Discord client
  config.py            # env / settings
  embed_parser.py      # разбор Ticket Tool embed
  pricing.py           # робуксы → рубли
  yoomoney_client.py   # Quickpay + operation-history
  ticket_flow.py       # сценарий тикета
  messages.py          # тексты сообщений
  webhook.py           # опциональные HTTP-уведомления ЮMoney
scripts/
  get_yoomoney_token.py  # одноразовый OAuth access_token
tests/                 # unit-тесты
```

## Architecture

```
Discord events → ticket_flow → pricing + yoomoney_client
                              ↘ payment poll / webhook → confirm or close
```

### Key conventions

- Секреты только в `.env` (см. `.env.example`)
- Бизнес-логика в `bot/*.py`, не в `main`
- Тексты покупателю — в `bot/messages.py` или через env-шаблоны
- Внешние HTTP-вызовы только в `yoomoney_client.py` / `webhook.py`

## Reference Files

| Pattern | Reference file |
|---------|---------------|
| Ticket flow | `bot/ticket_flow.py` |
| YooMoney API | `bot/yoomoney_client.py` |
| Embed parse | `bot/embed_parser.py` |
| Test | `tests/test_pricing.py` |

## Do Not Touch (without explicit request)

- Логика подписи HTTP-уведомлений ЮMoney (`bot/webhook.py`)
- Хранение `YOOMONEY_ACCESS_TOKEN` / Discord token вне `.env`

## Common Tasks

| Task | Steps |
|------|-------|
| Сменить тексты | править `bot/messages.py` или env `MSG_*` |
| Сменить курс | `ROBUX_RATE` в `.env` |
| Получить токен ЮMoney | `python scripts/get_yoomoney_token.py` |

## Environment

Copy `.env.example` to `.env` and fill values. Never commit `.env`.
