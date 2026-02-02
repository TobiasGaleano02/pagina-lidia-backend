import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Asuncion")
DEFAULT_BUFFER_MIN = int(os.getenv("DEFAULT_BUFFER_MIN", "10"))
