"""
ربات تلگرام دستیار مترجم
هر متنی که برایش بفرستید را با هوش مصنوعی Gemini (رایگان) ترجمه می‌کند.

- متن فارسی  → به انگلیسی ترجمه می‌شود
- متن غیرفارسی → به فارسی ترجمه می‌شود
- با دستور /to می‌توانید زبان مقصد ثابت انتخاب کنید (مثلاً /to French)
"""

import logging
import os

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
# برای ترجمه "فکر کردن" لازم نیست و فقط کندش می‌کند؛ خالی بگذارید تا پیش‌فرض مدل استفاده شود
GEMINI_THINKING = os.getenv("GEMINI_THINKING", "minimal").strip()
# اگر خالی نباشد، فقط این کاربر (آیدی عددی تلگرام) می‌تواند از ربات استفاده کند
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID", "").strip()

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise SystemExit("TELEGRAM_TOKEN و GEMINI_API_KEY را در فایل .env تنظیم کنید.")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

client = genai.Client(
    api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=60_000)
)
GEN_CONFIG = (
    types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=GEMINI_THINKING)
    )
    if GEMINI_THINKING
    else None
)

AUTO = "auto"
TELEGRAM_MAX_LEN = 4096


def build_prompt(text: str, target: str) -> str:
    if target == AUTO:
        rule = (
            "If the text is in Persian (Farsi), translate it into English. "
            "Otherwise, translate it into Persian (Farsi)."
        )
    else:
        rule = f"Translate the text into {target}."
    return (
        "You are a professional translator. "
        f"{rule} "
        "Keep the meaning, tone and formatting. "
        "Reply with ONLY the translation, no explanations, no quotes.\n\n"
        f"Text:\n{text}"
    )


def translate(text: str, target: str) -> str:
    response = client.models.generate_content(
        model=GEMINI_MODEL, contents=build_prompt(text, target), config=GEN_CONFIG
    )
    return (response.text or "").strip()


def is_allowed(update: Update) -> bool:
    if not ALLOWED_USER_ID:
        return True
    return str(update.effective_user.id) == ALLOWED_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "سلام! 👋 من دستیار مترجم شما هستم.\n\n"
        "هر متنی بفرستید ترجمه‌اش می‌کنم:\n"
        "• فارسی ← انگلیسی\n"
        "• هر زبان دیگر ← فارسی\n\n"
        "دستورها:\n"
        "/to French — ترجمه همیشه به زبان دلخواه\n"
        "/auto — برگشت به حالت خودکار\n"
        "/myid — نمایش آیدی عددی شما"
    )


async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    if not context.args:
        await update.message.reply_text("مثال: /to English  یا  /to German")
        return
    target = " ".join(context.args)
    context.user_data["target"] = target
    await update.message.reply_text(f"✅ از این به بعد به «{target}» ترجمه می‌کنم.")


async def set_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    context.user_data["target"] = AUTO
    await update.message.reply_text("✅ حالت خودکار فعال شد (فارسی ⇄ انگلیسی).")


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"آیدی عددی شما: {update.effective_user.id}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await update.message.reply_text("⛔ این ربات شخصی است.")
        return

    target = context.user_data.get("target", AUTO)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    try:
        result = translate(update.message.text, target)
    except Exception as e:  # noqa: BLE001
        log.exception("Translation failed")
        await update.message.reply_text(f"❌ خطا در ترجمه:\n{e}")
        return

    if not result:
        await update.message.reply_text("❌ ترجمه‌ای دریافت نشد، دوباره امتحان کنید.")
        return

    for i in range(0, len(result), TELEGRAM_MAX_LEN):
        await update.message.reply_text(result[i : i + TELEGRAM_MAX_LEN])


def ipv4_request() -> HTTPXRequest:
    # بعضی سرورها IPv6 خراب دارند و اتصال به تلگرام قطع می‌شود؛ فقط IPv4 استفاده می‌کنیم
    transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
    return HTTPXRequest(httpx_kwargs={"transport": transport})


def main() -> None:
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .request(ipv4_request())
        .get_updates_request(ipv4_request())
        .build()
    )
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("to", set_target))
    app.add_handler(CommandHandler("auto", set_auto))
    app.add_handler(CommandHandler("myid", my_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log.info("Bot is running... (Ctrl+C to stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
