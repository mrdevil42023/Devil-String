import logging
from typing import Union
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from StringGen.save_user import save_user
from StringGen.database import users

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def command_filter(cmd: Union[str, list]) -> filters.Filter:
    return filters.private & filters.incoming & filters.command(cmd)


@Client.on_message(command_filter(["start", "help"]))
async def start_handler(bot: Client, message: Message):
    user = message.from_user
    await save_user(user)

    try:
        bot_info = await bot.get_me()
        bot_name = bot_info.first_name or "This Bot"

        join_info = ""
        try:
            existing = await users.find_one({"_id": user.id})
            if existing and "joined" in existing:
                join_time = existing["joined"]
                if isinstance(join_time, str):
                    join_time = datetime.fromisoformat(join_time)
                if isinstance(join_time, datetime):
                    from datetime import timedelta, timezone
                    IST = timezone(timedelta(hours=5, minutes=30))
                    join_info = f"\n🕒 You joined: **{join_time.astimezone(IST).strftime('%d-%m-%Y %I:%M %p')} IST**"
        except Exception:
            logger.warning("Could not fetch user join info from DB")

        response_text = (
            f"👋 Hey {user.mention},\n\n"
            f"I am **{bot_name}** — a session generator bot.\n"
            "I can help you create sessions for **Pyrogram / Telethon**, user and bot accounts."
            f"{join_info}\n\n"
            "Tap **below** to begin ⬇️"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("⚙️ Generate Session", callback_data="generate")],
                [
                    InlineKeyboardButton(
                        "💬 Support", url="https://t.me/devilbotsupport"
                    ),
                    InlineKeyboardButton(
                        "📢 Channel", url="https://t.me/devilbots971"
                    ),
                ],
            ]
        )

        await message.reply_text(
            text=response_text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.exception("⚠️ Error in /start or /help handler:")
        await message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )
