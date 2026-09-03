"""
Контент воронки — ВСЁ, что бот отправляет, собрано здесь, чтобы менять в одном месте.

MVP: аудио пока заглушки-текстом. Чтобы заменить на реальное аудио — см. функции
send_material_1 / send_material_2 ниже: раскомментируй send_audio и впиши file_id.
Как получить file_id — в README в routes/funnel.py.
"""
from __future__ import annotations

from app.funnel import bot

# ─── Аудио материалов ─────────────────────────────────────────────────────────
# Как заполнить: отправь голосовое или аудио-файл боту @ai47_academy_bot —
# он ответит строкой вида "file_id (voice): AAA..." или "file_id (audio): BBB...".
# Скопируй file_id сюда и поставь KIND = тот тип, что бот назвал ("voice" или "audio").
# Пока file_id пустой — вместо аудио уходит текст-заглушка.
AUDIO_1_FILE_ID = "AwACAgUAAxkBAAICj2qZTHitc-p9FopHJH_FG2DWZePEAAKbKQACEPPRVI2LC94-QDqiPQQ"      # первый материал (после кнопки «Получить материалы»)
AUDIO_1_KIND = "voice"    # "voice" — голосовое, "audio" — mp3/аудио-файл
AUDIO_2_FILE_ID = ""      # второй материал (после «Забрать материалы» в оффере)
AUDIO_2_KIND = "voice"

# ─── Тексты ───────────────────────────────────────────────────────────────────
BTN_GET_MATERIALS = "📚 Получить материалы"
BTN_OPEN_LANDING = "📖 Открыть материалы"

WELCOME_TEXT = (
    "Привет! 👋\n\n"
    "Это бот с материалами по автоматизации.\n"
    "Жми кнопку ниже — пришлю первый материал 👇"
)

AFTER_MATERIAL_1_TEXT = (
    "Готово ✅\n\n"
    "Теперь открой лендинг с материалами — там вся подборка.\n"
    "Внутри жми «Узнать программу», и я пришлю следующий материал 👇"
)

# Заглушки на время MVP (потом заменятся реальным аудио)
PLACEHOLDER_AUDIO_1 = (
    "🎧 <b>[ЗДЕСЬ БУДЕТ АУДИО №1]</b>\n\n"
    "Пока заглушка — текст вместо голосового. После деплоя заменим на реальное аудио."
)
PLACEHOLDER_AUDIO_2 = (
    "🎧 <b>[ЗДЕСЬ БУДЕТ АУДИО №2 — материал из оффера]</b>\n\n"
    "Пока заглушка. Сюда прилетит материал после кнопки «Забрать материалы» в оффере."
)
PLACEHOLDER_FREEBIES = (
    "🎁 <b>[ЗДЕСЬ БУДУТ БЕСПЛАТНЫЕ МАТЕРИАЛЫ]</b>\n\n"
    "Пока заглушка для кнопки «Бесплатные материалы»."
)
BOOKING_TEXT = (
    "✅ <b>Место забронировано!</b>\n\n"
    "Скоро свяжемся с деталями. А пока можешь забрать материалы кнопкой «Забрать материалы»."
)


def _open_landing_keyboard(landing_url: str) -> dict:
    """Reply-клавиатура с web_app кнопкой. ВАЖНО: sendData из мини-аппа работает
    только если апп открыт ИМЕННО такой кнопкой (KeyboardButton + web_app)."""
    return {
        "keyboard": [[{"text": BTN_OPEN_LANDING, "web_app": {"url": landing_url}}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def _start_keyboard() -> dict:
    return {
        "keyboard": [[{"text": BTN_GET_MATERIALS}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }


async def send_welcome(chat_id: int) -> None:
    await bot.send_message(chat_id, WELCOME_TEXT, reply_markup=_start_keyboard())


async def _send_audio_or_placeholder(
    chat_id: int, file_id: str, kind: str, placeholder: str
) -> None:
    """Отправить голосовое/аудио по file_id; если file_id пуст — текст-заглушку."""
    if not file_id:
        await bot.send_message(chat_id, placeholder)
        return
    if kind == "audio":
        await bot.send_audio(chat_id, file_id)
    else:
        await bot.send_voice(chat_id, file_id)


async def send_material_1(chat_id: int, landing_url: str) -> None:
    """Первый материал + кнопка открыть лендинг."""
    await _send_audio_or_placeholder(chat_id, AUDIO_1_FILE_ID, AUDIO_1_KIND, PLACEHOLDER_AUDIO_1)
    await bot.send_message(
        chat_id, AFTER_MATERIAL_1_TEXT, reply_markup=_open_landing_keyboard(landing_url)
    )


async def send_material_2(chat_id: int) -> None:
    """Второй материал — после «Забрать материалы» в оффере."""
    await _send_audio_or_placeholder(chat_id, AUDIO_2_FILE_ID, AUDIO_2_KIND, PLACEHOLDER_AUDIO_2)


async def send_freebies(chat_id: int) -> None:
    await bot.send_message(chat_id, PLACEHOLDER_FREEBIES)


async def send_booking(chat_id: int) -> None:
    await bot.send_message(chat_id, BOOKING_TEXT)
