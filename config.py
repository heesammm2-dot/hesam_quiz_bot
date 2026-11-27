import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "hesam_quiz.sqlite3")
WIN_SCORE = 10
RATE_LIMIT_SECONDS = 1.0
