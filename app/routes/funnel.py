"""
Funnel-бот — публичная воронка выдачи материалов (отдельный токен FUNNEL_BOT_TOKEN).

Маршруты:
  POST /funnel/webhook   — апдейты Telegram (message, callback_query, web_app_data)
  GET  /funnel/landing   — лендинг-Mini App (app/funnel/landing.html)
  GET  /funnel/setup     — разовая установка webhook (?secret=FUNNEL_WEBHOOK_SECRET)

Сценарий:
  /start                       → приветствие + кнопка «📚 Получить материалы»
  «📚 Получить материалы»       → материал №1 (пока текст-заглушка) + кнопка открыть лендинг
  лендинг → «Узнать программу»  → web_app_data='program' → материал №2 (заглушка)
  лендинг → «Бесплатные …»      → web_app_data='freebies' → бесплатные материалы (заглушка)

Webhook защищён заголовком X-Telegram-Bot-Api-Secret-Token (если FUNNEL_WEBHOOK_SECRET задан).

═══════════════════════════════════════════════════════════════════════════════
КАК ЗАМЕНИТЬ ЗАГЛУШКИ НА РЕАЛЬНОЕ АУДИО (после деплоя):
  1) Отправь нужное аудио/голосовое СВОЕМУ funnel-боту обычным сообщением.
  2) Открой в браузере:
       https://<PUBLIC_BASE_URL>/funnel/last-file?secret=<FUNNEL_WEBHOOK_SECRET>
     (этот эндпоинт показывает file_id последнего полученного ботом медиа)
  3) Скопируй file_id в app/funnel/content.py → AUDIO_1_FILE_ID / AUDIO_2_FILE_ID.
  4) Закоммить и задеплой. Заглушка сама заменится на send_audio.
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.config import get_settings
from app.funnel import bot, content

logger = logging.getLogger(__name__)
router = APIRouter()

_FUNNEL_DIR = Path(__file__).resolve().parent.parent / "funnel"
_HTML_PATH = _FUNNEL_DIR / "landing.html"
_OFFER_PATH = _FUNNEL_DIR / "offer.html"
_WEB_PATH = _FUNNEL_DIR / "web.html"
_IMG_DIR = _FUNNEL_DIR / "img"

# Последний полученный ботом file_id медиа — для удобного получения file_id аудио.
_last_media: dict = {}


def _landing_url(request: Request) -> str:
    """Абсолютный https-URL лендинга для web_app кнопки."""
    s = get_settings()
    base = s.public_base_url or str(request.base_url).rstrip("/")
    # Telegram требует https для web_app
    if base.startswith("http://"):
        base = "https://" + base[len("http://"):]
    return f"{base}/funnel/landing"


@router.get("/landing", response_class=HTMLResponse)
async def landing() -> HTMLResponse:
    if not _HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="landing not found")
    html = _HTML_PATH.read_text(encoding="utf-8")
    # no-store: всегда свежая версия после деплоя (как в miniapp)
    return HTMLResponse(content=html, headers={"Cache-Control": "no-store, max-age=0"})


@router.get("/offer", response_class=HTMLResponse)
async def offer() -> HTMLResponse:
    """Страница оффера (программа интенсива + условия). Открывается из лендинга."""
    if not _OFFER_PATH.exists():
        raise HTTPException(status_code=404, detail="offer not found")
    html = _OFFER_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html, headers={"Cache-Control": "no-store, max-age=0"})


@router.get("/web", response_class=HTMLResponse)
async def web() -> HTMLResponse:
    """Публичная веб-версия оффер-лендинга (для внешнего хостинга/Vercel).
    Без Telegram Mini App-логики; кнопки «купить» ведут в клуб-бота."""
    if not _WEB_PATH.exists():
        raise HTTPException(status_code=404, detail="web not found")
    html = _WEB_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html, headers={"Cache-Control": "no-store, max-age=0"})


@router.get("/img/{name}")
async def img(name: str) -> FileResponse:
    """Отдать картинку лендинга. Защита от path traversal — только basename."""
    safe = Path(name).name
    path = _IMG_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/setup")
async def setup(secret: str = "") -> JSONResponse:
    """Разовая установка webhook funnel-бота. Защита простым секретом из env."""
    s = get_settings()
    if not s.funnel_webhook_secret or secret != s.funnel_webhook_secret:
        raise HTTPException(status_code=403, detail="bad secret")
    if not s.public_base_url:
        raise HTTPException(status_code=400, detail="PUBLIC_BASE_URL не задан")
    webhook_url = f"{s.public_base_url}/funnel/webhook"
    res = await bot.set_webhook(webhook_url, secret_token=s.funnel_webhook_secret)
    # Заодно поставим команду /start в меню бота
    try:
        await bot.set_my_commands([{"command": "start", "description": "Получить материалы"}])
    except Exception:
        logger.exception("funnel set_my_commands fail")
    return JSONResponse({"webhook": webhook_url, "telegram": res})


@router.get("/last-file")
async def last_file(secret: str = "") -> JSONResponse:
    """Показать file_id последнего медиа, присланного боту (для подстановки аудио)."""
    s = get_settings()
    if not s.funnel_webhook_secret or secret != s.funnel_webhook_secret:
        raise HTTPException(status_code=403, detail="bad secret")
    return JSONResponse(_last_media or {"info": "пришли боту аудио/голосовое и обнови страницу"})


@router.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
) -> JSONResponse:
    s = get_settings()
    if not s.funnel_bot_token:
        return JSONResponse({"ok": True, "skip": "no funnel token"})

    # Проверка секрета вебхука
    if s.funnel_webhook_secret and x_telegram_bot_api_secret_token != s.funnel_webhook_secret:
        raise HTTPException(status_code=403, detail="bad webhook secret")

    try:
        update = await request.json()
    except Exception:
        return JSONResponse({"ok": True})

    try:
        await _handle_update(update, request)
    except Exception:
        logger.exception("funnel webhook handler fail")
    # Telegram всегда отдаём 200, иначе будет долбить ретраями
    return JSONResponse({"ok": True})


async def _handle_update(update: dict, request: Request) -> None:
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    # 1) Данные из мини-аппа (нажали кнопку «Узнать программу» / «Бесплатные …»)
    web_app_data = msg.get("web_app_data")
    if web_app_data:
        payload = (web_app_data.get("data") or "").strip()
        if payload == "book":
            await content.send_booking(chat_id)
        elif payload == "freebies":
            await content.send_freebies(chat_id)
        else:
            # program и всё остальное → выдаём материал из оффера
            await content.send_material_2(chat_id)
        return

    # 2) Запоминаем file_id присланного медиа (удобно вытащить аудио file_id)
    for key in ("audio", "voice", "video", "document"):
        media = msg.get(key)
        if media and media.get("file_id"):
            _last_media.clear()
            _last_media.update({"type": key, "file_id": media["file_id"], "from_chat": chat_id})
            await bot.send_message(
                chat_id,
                f"file_id ({key}):\n<code>{media['file_id']}</code>",
            )
            return

    text = (msg.get("text") or "").strip()

    # 3) /start
    if text.startswith("/start"):
        await content.send_welcome(chat_id)
        return

    # 4) Кнопка «Получить материалы»
    if text == content.BTN_GET_MATERIALS:
        await content.send_material_1(chat_id, _landing_url(request))
        return

    # 5) Любой другой текст — мягко направляем
    await content.send_welcome(chat_id)
