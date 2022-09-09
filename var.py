from decouple import config
from dotenv import load_dotenv

load_dotenv()


class Var:
    API_ID = config("API_ID", default=6, cast=int)
    API_HASH = config("API_HASH", default="eb06d4abfb49dc3eeb1aeb98ae0f581e")
    BOT_TOKEN = config("BOT_TOKEN", default=None)
    CHAT = config("CHAT", default="{}")
    REDIS_URI = config("REDIS_URI", default=None)
    REDIS_PASSWORD = config("REDIS_PASSWORD", default=None)
