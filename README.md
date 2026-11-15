# Annet Mouse — Twitch Stream Announcer

Бот автоматически публикует анонсы запланированных стримов Twitch-канала [annet_mouse](https://www.twitch.tv/annet_mouse) в Telegram и Discord.

## Как работает бот

- Получает расписание напрямую через Twitch Helix API.
- Проверяет расписание каждые 5 минут с помощью GitHub Actions.
- Публикует анонс за 120 минут до начала стрима.
- Использует часовой пояс Europe/Moscow (МСК).
- Отправляет одинаковое сообщение в Telegram и Discord.
- Сохраняет историю опубликованных анонсов в `posted.json`, чтобы избегать повторных публикаций.

**Формат сообщения:**

🎮 Название стрима

📅 Дата: ДД.ММ.ГГГГ  
🕒 Время: ЧЧ:ММ (МСК)

⚠️ Возможны изменения

Важно: GitHub Actions может запускать задания с задержкой относительно указанного расписания.

## Настройка Twitch

1. Открой [Twitch Developer Console](https://dev.twitch.tv/console/apps).
2. Создай приложение с категорией Application Integration.
3. Используй Redirect URL `http://localhost`.
4. Сохрани Client ID и Client Secret.

## Настройка Telegram

1. Открой Telegram и найди @BotFather.
2. Создай бота командой `/newbot`.
3. Сохрани выданный токен.
4. Добавь бота в нужный канал или группу.
5. Предоставь ему право отправлять сообщения.
6. Узнай ID канала или группы.

## Настройка Discord

1. Открой настройки нужного Discord-канала.
2. Перейди в Integrations → Webhooks.
3. Создай Webhook.
4. Скопируй URL вебхука.

## Добавление секретов GitHub

Открой репозиторий:

**Settings → Secrets and variables → Actions**

Нажми **New repository secret** и добавь следующие пять секретов:

| Имя секрета | Значение |
|---|---|
| `TWITCH_CLIENT_ID` | Client ID приложения Twitch |
| `TWITCH_CLIENT_SECRET` | Client Secret приложения Twitch |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `TELEGRAM_CHAT_ID` | ID Telegram-канала или группы |
| `DISCORD_WEBHOOK_URL` | URL Discord Webhook |

Не вставляй секреты непосредственно в код и не публикуй их в репозитории.

## Разрешения GitHub Actions

Открой:

**Settings → Actions → General → Workflow permissions**

Выбери **Read and write permissions** и сохрани изменения.

Это необходимо, чтобы workflow мог обновлять `posted.json` после отправки анонсов.

## Запуск

1. Убедись, что все пять секретов добавлены.
2. Открой вкладку **Actions**.
3. Выбери workflow **Twitch stream announcements**.
4. Нажми **Run workflow**.

Автоматические проверки выполняются каждые пять минут.

## Важные замечания

- Если расписание стрима изменилось до публикации анонса, бот использует актуальное расписание Twitch при следующей проверке.
- Если один сервис принял сообщение, а второй вернул ошибку, повторный запуск может привести к дублированию сообщения в первом сервисе.
- История отправленных анонсов хранится в `posted.json`.
