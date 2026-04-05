import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID") or "0")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID") or "0")
OPENSEARCH_URI = os.getenv("OPENSEARCH_URI")
