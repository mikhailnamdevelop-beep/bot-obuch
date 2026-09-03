"""
Funnel-бот — FastAPI entry point (самостоятельный проект).

Запуск локально:
    uvicorn app.main:app --reload --port 8080

На хостинге команда та же (порт берётся из $PORT — см. Procfile).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import __version__
from app.config import get_settings
from app.routes.funnel import router as funnel_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("funnel")
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    s = get_settings()
    logger.info("Funnel-бот стартует. env=%s base=%s", s.env, s.public_base_url or "(нет)")
    # Самовосстановление webhook: переустанавливаем на каждом старте, чтобы бот
    # не «отваливался», если webhook слетел. drop_pending=False — не терять апдейты.
    if s.funnel_bot_token and s.public_base_url:
        try:
            from app.funnel import bot as funnel_bot
            res = await funnel_bot.set_webhook(
                f"{s.public_base_url}/funnel/webhook",
                secret_token=s.funnel_webhook_secret or None,
                drop_pending=False,
            )
            logger.info("funnel webhook авто-установлен: %s", res.get("description") or res)
        except Exception:
            logger.exception("funnel webhook авто-установка не удалась (сервис всё равно стартует)")
    else:
        logger.warning("FUNNEL_BOT_TOKEN или PUBLIC_BASE_URL не заданы — webhook не ставлю.")
    yield
    logger.info("Funnel-бот останавливается.")


app = FastAPI(
    title="Funnel bot",
    version=__version__,
    description="Публичная воронка выдачи материалов (Telegram + Mini App)",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    s = get_settings()
    return JSONResponse({"status": "ok", "version": __version__, "env": s.env})


@app.get("/")
async def root():
    return {"name": "Funnel bot", "version": __version__}


# ─── Routes ──────────────────────────────────────────────────────────────────
app.include_router(funnel_router, prefix="/funnel", tags=["funnel"])
