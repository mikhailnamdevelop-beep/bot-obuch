# Funnel-бот (Telegram + Mini App)

Публичная воронка выдачи материалов: человек открывает бота → жмёт
«Получить материалы» → получает материал №1 → открывает Mini App лендинг →
внутри жмёт кнопку → получает материал №2 / переходит в клуб.

Раньше жил внутри проекта `daos`. Теперь это **самостоятельный проект** —
запускается и деплоится независимо.

---

## Структура

```
бот обуч/
├── app/
│   ├── main.py              FastAPI entry point (uvicorn app.main:app)
│   ├── config.py            настройки из .env (только funnel)
│   ├── funnel/
│   │   ├── bot.py           клиент Telegram Bot API (свой токен)
│   │   ├── content.py       ВСЕ тексты и логика аудио — меняется здесь
│   │   ├── landing.html     Mini App лендинг с гайдами (зум фото)
│   │   ├── offer.html       страница оффера: программа 6 дней, цены, CTA
│   │   └── img/             картинки лендинга и оффера
│   └── routes/
│       └── funnel.py        маршруты: webhook, /landing, /offer, /img, /setup, /last-file
├── requirements.txt
├── Procfile                 команда запуска для хостинга
├── .env.example            шаблон переменных (скопируй в .env)
├── .env                     рабочие секреты (в .gitignore, НЕ коммить)
├── карта развития/          исходные фото (материал для лендинга)
└── оффер/                   исходные фото оффера
```

---

## Переменные окружения (`.env`)

| Переменная | Зачем |
|---|---|
| `FUNNEL_BOT_TOKEN` | токен бота от @BotFather |
| `FUNNEL_ADMIN_ID` | твой Telegram ID (админ) |
| `FUNNEL_WEBHOOK_SECRET` | секрет для webhook и `/funnel/setup`, `/funnel/last-file` |
| `PUBLIC_BASE_URL` | публичный https-адрес сервиса (для Mini App и webhook) |
| `ENV` | `local` или `production` |

Значения уже перенесены в `.env`. Шаблон — в `.env.example`.

---

## Запуск локально

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Проверка: открой http://localhost:8080/health — должно быть `{"status":"ok",...}`.
Лендинг: http://localhost:8080/funnel/landing

> Webhook Telegram требует публичный **https**. Локально апдейты бота не придут
> без туннеля (ngrok/cloudflared) и `PUBLIC_BASE_URL`. Лендинг же смотрится локально.

---

## Деплой (Railway / любой хостинг с Procfile)

1. Залей папку в отдельный git-репозиторий.
2. Создай сервис на хостинге, подключи репозиторий.
3. Пропиши переменные окружения (из `.env`).
4. Задай `PUBLIC_BASE_URL` = публичный адрес сервиса (напр. `https://xxx.up.railway.app`).
5. После деплоя открой один раз:
   `https://<PUBLIC_BASE_URL>/funnel/setup?secret=<FUNNEL_WEBHOOK_SECRET>`
   — это зарегистрирует webhook и команду `/start`.

> Webhook также сам переустанавливается при каждом старте сервиса (self-heal
> в `app/main.py`), так что бот не «отваливается».

---

## Где что менять

- **Тексты бота, кнопки, заглушки** → `app/funnel/content.py`
- **Лендинг с гайдами** → `app/funnel/landing.html` + `app/funnel/img/`
- **Страница оффера (программа, цены)** → `app/funnel/offer.html`
- **Логика апдейтов (кто на что жмёт)** → `app/routes/funnel.py` (`_handle_update`)

### Как связаны две страницы

`/funnel/landing` — главная с гайдами. Все кнопки «Узнать программу» вызывают
`goOffer()` → переход на `/funnel/offer`. На странице оффера слева сверху кнопка
«← Назад» возвращает на лендинг.

Кнопки на странице оффера:
- ссылки «Присоединиться / Вступить» → клуб-бот `t.me/ai47club_bot?start=landing`
  (внутри Telegram открываются через `openTelegramLink`);
- «Получить бесплатный материал» → `sendData('freebies')` — Mini App закрывается,
  бот присылает материал в чат (обработчик `freebies` в `routes/funnel.py`).

> Картинки программы лежат в `app/funnel/img/prog-*.png`, фон — `img/bg-cosmic-mesh.jpg`.
> Фон весит ~1.7 МБ, а слайды по ~1.8 МБ каждый — если Mini App будет грузиться
> медленно на мобильном, стоит пережать их в WebP.

### Заменить текст-заглушки на реальное аудио

Сейчас аудио — заглушки текстом (MVP). Чтобы включить настоящее аудио:

1. Отправь голосовое/аудио своему боту обычным сообщением.
2. Открой `https://<PUBLIC_BASE_URL>/funnel/last-file?secret=<FUNNEL_WEBHOOK_SECRET>`
   — покажет `file_id` последнего медиа.
3. Впиши его в `app/funnel/content.py` → `AUDIO_1_FILE_ID` / `AUDIO_2_FILE_ID`
   (и `AUDIO_*_KIND` = `voice` или `audio`).
4. Передеплой.

---

## Важно про старый деплой

Бот раньше работал в составе `daos` на Railway. Если продолжаешь тут:
- деплой этот проект как **отдельный сервис** и переставь webhook (`/funnel/setup`);
- на один и тот же бот-токен webhook может указывать только на **один** адрес —
  как только настроишь новый сервис, старый (в составе daos) перестанет получать апдейты.
