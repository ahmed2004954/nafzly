import asyncio
import os

from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def build_message(project: dict) -> str:
    title = project.get("title", "—")
    url = project.get("url", "")
    raw = project.get("raw", "")

    return (
        f"🆕 <b>مشروع جديد على نفذلي</b>\n\n"
        f"📌 <b>{title}</b>\n"
        f"🔗 <a href='{url}'>فتح المشروع</a>"
    )


async def send_message(text: str):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False,
    )


def notify(project: dict):
    message = build_message(project)
    asyncio.run(send_message(message))
