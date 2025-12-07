import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LLM_BACKEND = os.getenv("LLM_BACKEND", "openai")  # or "openai"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DATA_DIR = os.getenv("DATA_DIR", "data")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "db/vec.db")
TOP_K = int(os.getenv("TOP_K", 4))
