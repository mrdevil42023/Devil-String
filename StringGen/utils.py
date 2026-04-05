import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

pending_users = {}


async def ask(client: Client, user_id: int, text: str, timeout: int = 60) -> Message:
    await client.send_message(user_id, text)

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    pending_users[user_id] = future

    try:
        return await asyncio.wait_for(future, timeout)
    except TimeoutError:
        pending_users.pop(user_id, None)
        await client.send_message(user_id, "⌛ Timeout. Cancelling...")
        raise
    except Exception:
        pending_users.pop(user_id, None)
        raise


@Client.on_message(filters.private & filters.text)
async def listen_for_reply(bot: Client, message: Message):
    future = pending_users.pop(message.chat.id, None)
    if future and not future.done():
        future.set_result(message)
