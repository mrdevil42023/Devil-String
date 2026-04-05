import os
import json
import logging
from datetime import datetime, timezone
from asyncio import TimeoutError
from typing import Optional

import config
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telethon import TelegramClient
from telethon.sessions import StringSession
from StringGen.utils import ask

from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
)
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    FloodWaitError,
    AuthRestartError,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

os.makedirs("StringsHolder", exist_ok=True)

ASK_QUES = "**☞ Choose a session type to generate ✔️**"
BUTTONS_QUES = [
    [
        InlineKeyboardButton("Pyrogram V1", callback_data="pyrogram_v1"),
        InlineKeyboardButton("Pyrogram V2", callback_data="pyrogram_v2"),
    ],
    [InlineKeyboardButton("Telethon", callback_data="telethon")],
    [
        InlineKeyboardButton("Pyrogram Bot", callback_data="pyrogram_bot"),
        InlineKeyboardButton("Telethon Bot", callback_data="telethon_bot"),
    ],
]
GEN_BUTTON = [[InlineKeyboardButton("Generate Session 🔑", callback_data="generate")]]


async def ask_or_cancel(
    bot: Client, uid: int, prompt: str, *, timeout: Optional[int] = None
) -> Optional[str]:
    try:
        m = await ask(bot, uid, prompt, timeout=timeout or 60)
    except TimeoutError:
        raise TimeoutError("Timeout – no reply for a while")

    tx = m.text.strip()
    if tx in ("/cancel", "/restart"):
        await bot.send_message(
            uid,
            "» Cancelled." if tx == "/cancel" else "» Restarting bot...",
            reply_markup=InlineKeyboardMarkup(GEN_BUTTON),
        )
        return None
    return tx


def save_to_cache(uid: int, string_: str, meta: dict) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"StringsHolder/{uid}_{ts}"
    with open(base + "_session.txt", "w") as f:
        f.write(string_)
    with open(base + "_info.json", "w") as f:
        json.dump(meta, f, indent=2)


def readable_error(exc: Exception) -> str:
    mapping = {
        (ApiIdInvalid, ApiIdInvalidError): "Invalid **API ID/HASH**.",
        (PhoneNumberInvalid, PhoneNumberInvalidError): "Invalid **phone number**.",
        (PhoneCodeInvalid, PhoneCodeInvalidError): "Wrong **OTP**.",
        (PhoneCodeExpired, PhoneCodeExpiredError): "**OTP** expired.",
        (PasswordHashInvalid, PasswordHashInvalidError): "Wrong **2-step password**.",
        (FloodWaitError,): "Flood wait – try later.",
        (AuthRestartError,): "Auth restart required. Start again.",
    }
    for group, txt in mapping.items():
        if isinstance(exc, group):
            return txt
    return f"Unknown error: {str(exc).replace('`', '')}"


@Client.on_message(
    filters.private & filters.command(["generate", "gen", "string", "str"])
)
async def cmd_generate(_, m: Message):
    await m.reply(ASK_QUES, reply_markup=InlineKeyboardMarkup(BUTTONS_QUES))


async def generate_session(
    bot: Client,
    msg: Message,
    *,
    telethon: bool = False,
    old_pyro: bool = False,
    is_bot: bool = False,
):
    uid = msg.chat.id
    uname = msg.from_user.username or "unknown"

    ses_type = (
        "Telethon"
        if telethon
        else ("Pyrogram V1" if old_pyro else "Pyrogram V2")
    )
    if is_bot:
        ses_type += " Bot"

    await msg.reply(f"» Starting **{ses_type}** session generation...")

    try:
        api_txt = await ask_or_cancel(bot, uid, "Send **API_ID** or /skip")
        if api_txt is None:
            return
        if api_txt == "/skip":
            api_id, api_hash = config.API_ID, config.API_HASH
        else:
            api_id = int(api_txt)
            api_hash_txt = await ask_or_cancel(bot, uid, "Send **API_HASH**")
            if api_hash_txt is None:
                return
            api_hash = api_hash_txt
    except TimeoutError as te:
        return await msg.reply(
            f"» {te}", reply_markup=InlineKeyboardMarkup(GEN_BUTTON)
        )
    except ValueError:
        return await msg.reply(
            "» **API_ID** must be numeric.",
            reply_markup=InlineKeyboardMarkup(GEN_BUTTON),
        )

    prompt = (
        "Send **Bot Token**\n`123456:ABCDEF`"
        if is_bot
        else "Send **Phone Number**\n`+91xxxxxxxxxx`"
    )
    try:
        token_or_phone = await ask_or_cancel(bot, uid, prompt)
        if (
            token_or_phone is None
            or not token_or_phone.strip()
            or token_or_phone.strip() in [".", "-", "_"]
        ):
            return await msg.reply(
                "» Invalid phone number/token.",
                reply_markup=InlineKeyboardMarkup(GEN_BUTTON),
            )
        token_or_phone = token_or_phone.strip()
    except TimeoutError as te:
        return await msg.reply(
            f"» {te}", reply_markup=InlineKeyboardMarkup(GEN_BUTTON)
        )

    client = (
        TelegramClient(StringSession(), api_id, api_hash)
        if telethon
        else Client(
            "bot" if is_bot else "user",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=token_or_phone if is_bot else None,
            in_memory=True,
        )
    )

    try:
        await client.connect()
    except Exception as exc:
        logger.exception("connect failed")
        return await msg.reply(
            readable_error(exc), reply_markup=InlineKeyboardMarkup(GEN_BUTTON)
        )

    try:
        if is_bot:
            if telethon:
                await client.start(bot_token=token_or_phone)
            else:
                await client.sign_in_bot(token_or_phone)
        else:
            code = await (
                client.send_code_request(token_or_phone)
                if telethon
                else client.send_code(token_or_phone)
            )
            otp = await ask_or_cancel(
                bot, uid, "Send **OTP** (space-separated: `1 2 3 4 5`)", timeout=600
            )
            if otp is None:
                return
            otp = otp.replace(" ", "")
            try:
                if telethon:
                    await client.sign_in(token_or_phone, otp)
                else:
                    await client.sign_in(token_or_phone, code.phone_code_hash, otp)
            except (SessionPasswordNeeded, SessionPasswordNeededError):
                pw = await ask_or_cancel(
                    bot, uid, "Send **2-step verification password**", timeout=300
                )
                if pw is None:
                    return
                if telethon:
                    await client.sign_in(password=pw)
                else:
                    await client.check_password(password=pw)

    except Exception as exc:
        await client.disconnect()
        return await msg.reply(
            readable_error(exc), reply_markup=InlineKeyboardMarkup(GEN_BUTTON)
        )

    try:
        string_session = (
            client.session.save()
            if telethon
            else await client.export_session_string()
        )
    except Exception as exc:
        await client.disconnect()
        return await msg.reply(
            readable_error(exc), reply_markup=InlineKeyboardMarkup(GEN_BUTTON)
        )

    save_to_cache(
        uid,
        string_session,
        {
            "session_type": ses_type,
            "user_id": uid,
            "username": uname,
            "is_bot": is_bot,
            "is_telethon": telethon,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    try:
        note = (
            f"**Your {ses_type} Session:**\n\n`{string_session}`\n\n"
            "**⚠️ WARNING:** Never share this session string with anyone!"
        )
        if is_bot:
            await bot.send_message(uid, note)
        else:
            await client.send_message("me", note)
            await bot.send_message(
                uid, "✅ Session sent to your **Saved Messages**."
            )
    finally:
        await client.disconnect()
