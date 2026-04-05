import logging
import time
from pyrogram import Client, idle
from pyrogram.errors import ApiIdInvalid, ApiIdPublishedFlood, AccessTokenInvalid
import config
from StringGen.database import ensure_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

StartTime = time.time()

app = Client(
    name="String-Bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    in_memory=True,
    plugins=dict(root="StringGen"),
)


async def main():
    async with app:
        await ensure_index()
        uname = (await app.get_me()).username
        print(f"✅ Bot @{uname} is now ready to generate sessions.")
        await idle()


def run():
    print("🔧 Starting Session Generator Bot...")
    print(f"   API_ID   : {config.API_ID}")
    print(f"   API_HASH : {'set' if config.API_HASH else 'MISSING'}")
    print(f"   BOT_TOKEN: {'set' if config.BOT_TOKEN else 'MISSING'}")
    print(f"   OWNER_ID : {config.OWNER_ID}")
    print(f"   OPENSEARCH_URI: {'set' if config.OPENSEARCH_URI else 'MISSING'}")

    if not config.API_ID:
        logging.critical("❌ API_ID is not set or is 0.")
        return
    if not config.API_HASH:
        logging.critical("❌ API_HASH is not set.")
        return
    if not config.BOT_TOKEN:
        logging.critical("❌ BOT_TOKEN is not set.")
        return
    if not config.OPENSEARCH_URI:
        logging.critical("❌ OPENSEARCH_URI is not set.")
        return

    try:
        app.run(main())
    except ApiIdInvalid:
        logging.critical("❌ Invalid API_ID or API_HASH.")
    except ApiIdPublishedFlood:
        logging.critical("❌ API_ID is published flood.")
    except AccessTokenInvalid:
        logging.critical("❌ Invalid BOT_TOKEN.")
    except Exception as e:
        logging.critical(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    run()
