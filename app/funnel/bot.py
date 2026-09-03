"""
Telegram Bot API клиент для FUNNEL-бота (отдельный токен FUNNEL_BOT_TOKEN).

Намеренно НЕ переиспользует app/integrations/telegram.py — тот завязан на
личный DAOS-токен. Здесь свой минимальный httpx-клиент под публичную воронку.

Готовы хелперы send_audio / send_document — чтобы потом заменить текстовые
заглушки на реальное аудио одной строкой (см. README в routes/funnel.py).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


def _token() -> str:
    s = get_settings()
    if not s.funnel_bot_token:
        raise RuntimeError("FUNNEL_BOT_TOKEN не задан")
    return s.funnel_bot_token


def _base_url() -> str:
    return f"{API_BASE}/bot{_token()}"


async def _post(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{_base_url()}/{method}", json=payload)
        r.raise_for_status()
        return r.json()


async def send_message(
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = "HTML",
    reply_markup: Optional[dict[str, Any]] = None,
    disable_web_page_preview: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text or "...",
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return await _post("sendMessage", payload)


async def send_audio(
    chat_id: int,
    audio: str,
    caption: Optional[str] = None,
    parse_mode: Optional[str] = "HTML",
    reply_markup: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Отправить аудио. `audio` = file_id (рекомендуется) ИЛИ публичный https-URL на .mp3/.ogg.
    file_id получается так: отправь аудио своему боту руками, в апдейте будет
    message.audio.file_id — он стабилен и переиспользуется навсегда.
    """
    payload: dict[str, Any] = {"chat_id": chat_id, "audio": audio}
    if caption:
        payload["caption"] = caption
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return await _post("sendAudio", payload)


async def send_voice(chat_id: int, voice: str, caption: Optional[str] = None) -> dict[str, Any]:
    """Голосовое (.ogg/opus). voice = file_id или https-URL."""
    payload: dict[str, Any] = {"chat_id": chat_id, "voice": voice}
    if caption:
        payload["caption"] = caption
    return await _post("sendVoice", payload)


async def send_document(
    chat_id: int,
    document: str,
    caption: Optional[str] = None,
    parse_mode: Optional[str] = "HTML",
) -> dict[str, Any]:
    """Документ (PDF и т.п.). document = file_id или https-URL."""
    payload: dict[str, Any] = {"chat_id": chat_id, "document": document}
    if caption:
        payload["caption"] = caption
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return await _post("sendDocument", payload)


async def answer_callback_query(callback_query_id: str, text: Optional[str] = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text[:200]
    return await _post("answerCallbackQuery", payload)


async def set_webhook(
    url: str, secret_token: Optional[str] = None, drop_pending: bool = True
) -> dict[str, Any]:
    """Настройка вебхука funnel-бота. /funnel/setup сбрасывает очередь (drop_pending=True),
    авто-переустановка на старте — нет (drop_pending=False), чтобы не терять сообщения."""
    payload: dict[str, Any] = {
        "url": url,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": drop_pending,
    }
    if secret_token:
        payload["secret_token"] = secret_token
    return await _post("setWebhook", payload)


async def set_my_commands(commands: list[dict[str, str]]) -> dict[str, Any]:
    return await _post("setMyCommands", {"commands": commands})
