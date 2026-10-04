import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache"
LANGUAGE = "en-IN"
MAX_PAGES = 10
VERIFY_THRESHOLD = 85  # rapidfuzz score (0-100) to call a clause "verified"


def get_api_key() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key or key == "your_key_here":
        raise RuntimeError("SARVAM_API_KEY missing. Copy .env.example to .env and set it.")
    return key
