import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

MIDAS_MAPI_KEY = os.getenv("MIDAS_MAPI_KEY")
MIDAS_BASE_URL = os.getenv("MIDAS_BASE_URL")


def validate_config():
    missing = []

    if not MIDAS_MAPI_KEY:
        missing.append("MIDAS_MAPI_KEY")

    if not MIDAS_BASE_URL:
        missing.append("MIDAS_BASE_URL")

    if missing:
        raise ValueError(
            f"Missing variables in .env file: {', '.join(missing)}. "
            f"Expected .env at: {ENV_PATH}"
        )