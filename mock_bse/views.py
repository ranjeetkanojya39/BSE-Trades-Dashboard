"""
Mock BSE Exchange API  ->  GET /getTrades?page=N

Poori pull ka time PULL_DELAY_SECONDS (default 900 = 15 min). Data pages me aata hai
aur har page request me (delay / total_pages) seconds lagte hain, isliye koi bhi
HTTP connection ~25s se zyada open nahi rehta (network 30s pe kill kar deta hai).
"""
import math
import random
import time
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.http import JsonResponse

MAX_CONN_SECONDS = 25

TOTAL_TRADES = settings.TOTAL_TRADES
_pages_needed = max(1, math.ceil(settings.PULL_DELAY_SECONDS / MAX_CONN_SECONDS))
PAGE_SIZE = max(1, min(settings.PAGE_SIZE, math.ceil(TOTAL_TRADES / _pages_needed)))
TOTAL_PAGES = math.ceil(TOTAL_TRADES / PAGE_SIZE)
PER_PAGE_DELAY = settings.PULL_DELAY_SECONDS / TOTAL_PAGES

CLIENTS = ["Reliance Securities", "HDFC Securities", "Zerodha Broking", "ICICI Direct",
           "Kotak Securities", "Angel One", "Motilal Oswal", "Axis Direct"]
SYMBOLS = {"RELIANCE": 2900, "TCS": 3900, "INFY": 1500, "HDFCBANK": 1650,
           "ICICIBANK": 1100, "SBIN": 780, "ITC": 430, "LT": 3500,
           "BHARTIARTL": 1200, "WIPRO": 480, "TATAMOTORS": 950, "MARUTI": 12000}

_rng = random.Random(42)           # seed fixed => har baar same data
_now = datetime.now(timezone.utc)
TRADES = []
for i in range(1, TOTAL_TRADES + 1):
    sym = _rng.choice(list(SYMBOLS))
    TRADES.append({
        "trade_id": f"BSE{i:07d}",
        "client": _rng.choice(CLIENTS),
        "symbol": sym,
        "quantity": _rng.randint(1, 500) * 10,
        "price": round(SYMBOLS[sym] * _rng.uniform(0.97, 1.03), 2),
        "timestamp": (_now - timedelta(seconds=(TOTAL_TRADES - i) * 7)).isoformat(),
    })


def info(request):
    return JsonResponse({"total_trades": TOTAL_TRADES, "total_pages": TOTAL_PAGES,
                         "page_size": PAGE_SIZE, "per_page_delay_s": round(PER_PAGE_DELAY, 2),
                         "full_pull_s": settings.PULL_DELAY_SECONDS})


def get_trades(request):
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 0
    if page < 1 or page > TOTAL_PAGES:
        return JsonResponse({"error": "page out of range"}, status=404)
    time.sleep(PER_PAGE_DELAY)      # slow exchange ka simulation
    start = (page - 1) * PAGE_SIZE
    return JsonResponse({"page": page, "total_pages": TOTAL_PAGES, "total_records": TOTAL_TRADES,
                         "trades": TRADES[start:start + PAGE_SIZE]})
