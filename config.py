import os

from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "")
IMAP_PORT = os.getenv("IMAP_PORT", "")
EMAIL_LOGIN = os.getenv("EMAIL_LOGIN", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "")
TOKEN_URL = os.getenv("TOKEN_URL", "")