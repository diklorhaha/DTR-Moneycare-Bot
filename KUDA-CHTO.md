# Куда что вставлять (коротко)

## 1. Amvera → Переменные (секреты)

Вставь туда эти имена и значения (как в `.env`, но через кабинет Amvera):

| Имя | Откуда взять | Пример смысла |
|-----|----------------|---------------|
| `DISCORD_BOT_TOKEN` | Discord Developer Portal → Bot → Token | токен бота |
| `YOOMONEY_WALLET` | номер кошелька ЮMoney | `41001…` |
| `YOOMONEY_ACCESS_TOKEN` | один раз скриптом `scripts/get_yoomoney_token.py` | длинная строка |
| `ROBUX_RATE` | ваш курс | `2` → 2000 R$ = 1000 ₽ |
| `YOOMONEY_WEBHOOK_ENABLED` | включить уведомления | `true` |
| `YOOMONEY_WEBHOOK_HOST` | слушать все интерфейсы | `0.0.0.0` |
| `YOOMONEY_WEBHOOK_PORT` | порт внутри Amvera | `80` |
| `YOOMONEY_NOTIFICATION_SECRET` | ЮMoney → HTTP-уведомления → «Показать секрет» | секретное слово |

Остальное (`MSG_*`, таймауты) можно не трогать.

`YOOMONEY_CLIENT_ID` / `CLIENT_SECRET` в Amvera **не обязательны** — они нужны только локально, чтобы один раз получить `YOOMONEY_ACCESS_TOKEN`.

## 2. ЮMoney → HTTP-уведомления

**Второй домен регистрировать не надо.**

1. В Amvera открой проект → **Домены** → бесплатный домен вида  
   `https://dtr-moneycare.dtrshop.amvera.io`  
   (если имя другое — бери то, что показывает Amvera).
2. В ЮMoney в настройках HTTP-уведомлений вставь URL:

```text
https://dtr-moneycare.dtrshop.amvera.io/yoomoney/notification
```

3. Скопируй секрет → в Amvera переменная `YOOMONEY_NOTIFICATION_SECRET`.
4. Включи отправку уведомлений, сохрани.

После оплаты ЮMoney дергает этот URL → бот сразу пишет «оплата получена».  
Если webhook выключен, бот всё равно работает — просто опрашивает историю раз в N секунд.

## 3. Discord

1. Bot → включи **Message Content Intent**.
2. Пригласи бота на сервер с правами: читать/писать сообщения, читать историю, Manage Channels (если надо закрывать тикет).
3. Бот должен видеть те же `ticket-*` каналы, что Ticket Tool.

## 4. Порядок запуска

1. Заполни переменные в Amvera.
2. Залей код (`git push` в Amvera).
3. Дождись статуса «Запущено».
4. Проверь health: `https://ТВОЙ-ДОМЕН.amvera.io/health` → должно быть `ok`.
5. Создай тестовый тикет.
