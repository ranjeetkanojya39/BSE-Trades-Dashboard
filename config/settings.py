import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-secret-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "trades",
    "mock_bse",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"          # dashboard (port 8000)
WSGI_APPLICATION = "config.wsgi.application"

DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "db.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_PATH,
        "OPTIONS": {"timeout": 20},   # background thread + requests ek saath DB use karte hain
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Asia/Kolkata"

# ---- Dashboard config ----
BSE_URL = os.getenv("BSE_URL", "http://localhost:8001")
AUTO_PULL_ON_START = os.getenv("AUTO_PULL_ON_START", "true").lower() == "true"
STREAM_MAX_SECONDS = 25     # SSE stream 25s me band (network 30s pe kill karta hai), browser auto-reconnect

# ---- Mock BSE config ----
PULL_DELAY_SECONDS = float(os.getenv("PULL_DELAY_SECONDS", "900"))   # 900 = 15 min
TOTAL_TRADES = int(os.getenv("TOTAL_TRADES", "3000"))
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "60"))
