# Бот на Amvera — инструкция «для самых маленьких»

Ниже только кнопки и куда что вписать. Без теории.

Проект уже готов: код в папке `ticket-yoomoney-bot`, файл `amvera.yml` есть.

---

## Что должно быть у тебя ДО Amvera

Собери 4 вещи (блокнот):

1. **Discord Bot Token**  
   Сайт: https://discord.com/developers/applications → своё приложение → Bot → Reset/Copy Token.

2. **Номер кошелька ЮMoney**  
   Например `41001…`

3. **YOOMONEY_ACCESS_TOKEN**  
   Это длинная строка. Один раз получаешь на своём ПК:

   ```bash
   cd C:\Users\Бебрик\Projects\ticket-yoomoney-bot
   .\.venv\Scripts\activate
   python scripts/get_yoomoney_token.py --client-id ТВОЙ_CLIENT_ID --client-secret ТВОЙ_SECRET --redirect-uri https://localhost
   ```

   Скрипт даст ссылку → открой → разреши → скопируй URL из браузера обратно в скрипт → он напечатает `YOOMONEY_ACCESS_TOKEN=...`  
   Сохрани эту строку.

4. **Курс**  
   Например `2` (тогда 2000 робаксов = 1000 ₽).

---

## Шаг 1. Создай проект в Amvera

1. Зайди на https://cloud.amvera.ru  
2. **Создать проект**  
3. Имя можешь оставить своё (у вас уже было `dtr-moneycare`)  
4. Тип: приложение / Python (если спросят)  
5. Дойди до шага **Загрузка данных**

---

## Шаг 2. Залей код

### Вариант А — через git Amvera (проще для новичка)

На странице Amvera будет что-то вроде:

```text
git clone https://git.msk0.amvera.ru/dtrshop/dtr-moneycare
```

На своём ПК в PowerShell:

```bash
cd C:\Users\Бебрик\Projects\ticket-yoomoney-bot

git add .
git commit -m "bot ready for amvera"

git remote remove amvera
git remote add amvera https://git.msk0.amvera.ru/dtrshop/dtr-moneycare

git push -u amvera master
```

Если Amvera просит логин/пароль — это логин Amvera и **пароль для git** (или токен) из их подсказок, не Discord.

Если ветка у них `main`, а у тебя `master`:

```bash
git push -u amvera master:main
```

### Вариант Б — через GitHub

1. Залей этот проект на GitHub  
2. В Amvera выбери GitHub → вставь Personal Access Token → Выбери репозиторий → Подключить  

---

## Шаг 3. Впиши переменные (самое важное)

Amvera → твой проект → **Переменные** → добавить:

| Имя | Значение |
|-----|----------|
| `DISCORD_BOT_TOKEN` | токен Discord |
| `YOOMONEY_WALLET` | номер кошелька |
| `YOOMONEY_ACCESS_TOKEN` | длинный токен из скрипта |
| `ROBUX_RATE` | `2` (или свой курс) |
| `YOOMONEY_WEBHOOK_ENABLED` | `true` |
| `YOOMONEY_WEBHOOK_HOST` | `0.0.0.0` |
| `YOOMONEY_WEBHOOK_PORT` | `80` |
| `YOOMONEY_NOTIFICATION_SECRET` | пока оставь пустым — заполним на шаге 5 |

Сохрани. Перезапусти приложение, если Amvera просит.

---

## Шаг 4. Домен Amvera (второй домен НЕ нужен)

1. Amvera → проект → **Домены**  
2. Добавь **бесплатный домен Amvera**  
3. Получишь адрес вида:

```text
https://dtr-moneycare.dtrshop.amvera.io
```

Скопируй его целиком. Это и есть твой публичный URL.

Проверка после запуска бота:

```text
https://ТВОЙ-ДОМЕН.amvera.io/health
```

В браузере должно быть просто: `ok`

Если не `ok` — бот ещё не запущен или порт неверный (должен быть `80` в переменных и в `amvera.yml`).

---

## Шаг 5. HTTP-уведомления ЮMoney

1. Зайди в настройки кошелька ЮMoney → **HTTP-уведомления**  
2. В поле URL вставь (подставь СВОЙ домен из шага 4):

```text
https://dtr-moneycare.dtrshop.amvera.io/yoomoney/notification
```

3. Нажми **Показать секрет** → скопируй  
4. Вернись в Amvera → Переменные →  
   `YOOMONEY_NOTIFICATION_SECRET` = этот секрет  
5. В ЮMoney включи отправку уведомлений → Сохранить  
6. Перезапусти проект в Amvera

Готово: когда клиент оплатил, ЮMoney стучится в этот URL → бот пишет в тикет «оплата получена».

---

## Шаг 6. Discord — чтобы бот видел тикеты

1. https://discord.com/developers/applications → Bot  
2. Включи **MESSAGE CONTENT INTENT** → Save  
3. OAuth2 → URL Generator → scopes: `bot`  
   Права минимум:
   - View Channels  
   - Send Messages  
   - Read Message History  
   - Manage Channels (чтобы закрывать тикет по таймауту)  
4. Открой ссылку, добавь бота на сервер  
5. Роли/права: бот должен заходить в каналы `ticket-...` так же, как Ticket Tool / staff

---

## Шаг 7. Проверка «жив ли бот»

1. Amvera → статус приложения **Запущено** (не ошибка сборки)  
2. Открой `/health` → `ok`  
3. Создай тестовый тикет Ticket Tool с суммой робаксов  
4. Бот должен сам прислать ссылку на оплату  
5. Оплати маленькую сумму → бот должен написать об успехе  

Если ссылка есть, а «успех» не приходит:
- проверь URL уведомлений (без опечаток, именно `/yoomoney/notification`)
- проверь секрет
- в логах Amvera посмотри ошибки

---

## Частые ошибки

| Проблема | Что сделать |
|----------|-------------|
| Сборка падает | в корне есть `requirements.txt` и `amvera.yml` |
| `/health` не открывается | домен не добавлен / порт не 80 / приложение не Running |
| Бот молчит в тикете | нет Message Content Intent или нет прав на канал |
| Оплата есть, бот молчит | неверный URL/секрет уведомлений ЮMoney |
| Не знаю куда токены | только Amvera → **Переменные**, не в код и не в git |

---

## Что бот делает сам (команды писать не надо)

1. Увидел канал `ticket-...`  
2. Прочитал «Сумма робуксов для покупки»  
3. Посчитал рубли (`робаксы / ROBUX_RATE`)  
4. Прислал ссылку ЮMoney  
5. Получил HTTP-уведомление об оплате → написал «оплата получена»  
6. Если не оплатили вовремя → закрыл тикет  

Никаких `/pay` и ручных команд от покупателя не нужно.
