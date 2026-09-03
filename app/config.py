"""
Конфигурация funnel-бота (самостоятельный проект).

Локально:  читает из .env (python-dotenv).
На хостинге (Railway и т.п.): переменные приходят из окружения сервиса.

Все настройки — только то, что нужно воронке. Личный DAOS-бот сюда НЕ входит.
"""
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

# Локально подхватываем .env; в проде .env может не быть — это ок.
load_dotenv(override=False)


def _get(name: str, default: Optional[str] = None) -> str:
    val = os.getenv(name, default)
    return val if val is not None else ""


@dataclass(frozen=True)
class Settings:
    # ─── Окружение ───────────────────────────────────────────────
    env: str = field(default_factory=lambda: _get("ENV", "local"))
    log_level: str = field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))

    # ─── Funnel bot ──────────────────────────────────────────────
    # Свой токен, свой webhook /funnel/webhook, свой лендинг-Mini App /funnel/landing.
    funnel_bot_token: str = field(default_factory=lambda: _get("FUNNEL_BOT_TOKEN", ""))
    funnel_admin_id: int = field(default_factory=lambda: int(_get("FUNNEL_ADMIN_ID", "0") or "0"))
    funnel_webhook_secret: str = field(default_factory=lambda: _get("FUNNEL_WEBHOOK_SECRET", ""))
    # Публичный https-base сервиса (для url Mini App). Напр. https://xxx.up.railway.app
    public_base_url: str = field(default_factory=lambda: (_get("PUBLIC_BASE_URL", "") or "").rstrip("/"))

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Кешированный синглтон настроек."""
    return Settings()
