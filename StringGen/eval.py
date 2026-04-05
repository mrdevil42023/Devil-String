import os
import re
import sys
import traceback
from time import time
from io import StringIO
from inspect import getfullargspec

from pyrogram import Client, filters
from pyrogram.types import Message

from config import OWNER_ID


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message):"
        + "".join(f"\n {line}" for line in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


@Client.on_message(
    filters.command("eval")
    & filters.user(OWNER_ID)
    & ~filters.forwarded
    & ~filters.via_bot
)
async def executor(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("`No code provided.`")

    code = message.text.split(None, 1)[1]
    reply = await message.reply_text("`Processing...`")

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None

    try:
        await aexec(code, client, message)
    except Exception:
        exc = traceback.format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = exc or stderr or stdout or "Success"
    final_output = (
        f"**Code:**\n`{code}`\n\n"
        f"**Output:**\n`{evaluation}`"
    )

    if len(final_output) > 4096:
        with open("output.txt", "w") as f:
            f.write(final_output)
        await reply.delete()
        await message.reply_document("output.txt", caption="Output too long.")
        os.remove("output.txt")
    else:
        await reply.edit(final_output)
