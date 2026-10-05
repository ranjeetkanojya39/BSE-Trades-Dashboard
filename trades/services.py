"""
Background pull + event bus.

- start_pull()  : background THREAD me pull chalata hai (request/response se alag)
- publish()     : events (naye trades, status) memory me rakhta hai; SSE view inhe browser ko push karta hai
"""
import threading
import time
import uuid
from collections import deque

import requests
from django.conf import settings
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime

from .models import Trade

# ---------- Event bus ----------
_cond = threading.Condition()
EVENTS = deque(maxlen=2000)          # (id, event_name, data)
_seq = int(time.time() * 1000)       # restart ke baad bhi ids badhte rahein


def publish(event, data):
    global _seq
    with _cond:
        _seq += 1
        EVENTS.append((_seq, event, data))
        _cond.notify_all()


def latest_event_id():
    with _cond:
        return EVENTS[-1][0] if EVENTS else _seq


def wait_for_events(last_id, timeout):
    """last_id ke baad ke events return karta hai; nahi hain to timeout tak wait."""
    with _cond:
        if not any(e[0] > last_id for e in EVENTS):
            _cond.wait(timeout=max(timeout, 0))
        return [e for e in EVENTS if e[0] > last_id]


# ---------- Pull state ----------
STATE = {"status": "idle", "job_id": None, "page": 0, "total_pages": 0,
         "error": None, "started_at": None, "finished_at": None}
_start_lock = threading.Lock()


def snapshot():
    return {**STATE, "total_in_db": Trade.objects.count()}


def save_trades(trades):
    """Naye trades save karta hai (duplicate trade_id skip). Sirf naye wale return."""
    new = []
    with transaction.atomic():
        for t in trades:
            obj, created = Trade.objects.get_or_create(
                trade_id=t["trade_id"],
                defaults={"client": t["client"], "symbol": t["symbol"], "quantity": t["quantity"],
                          "price": t["price"], "timestamp": parse_datetime(t["timestamp"])})
            if created:
                new.append(obj.to_dict())
    return new


def fetch_page(session, page):
    for attempt in range(3):                      # 3 retries, exponential backoff
        try:
            # read timeout 28s: kabhi bhi 30s network limit cross nahi karega
            r = session.get(f"{settings.BSE_URL}/getTrades", params={"page": page}, timeout=(5, 28))
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def run_pull(job_id):
    STATE.update(status="running", job_id=job_id, page=0, total_pages=0,
                 error=None, started_at=time.time(), finished_at=None)
    publish("status", snapshot())
    try:
        with requests.Session() as session:
            page, total_pages = 1, 1
            while page <= total_pages:
                body = fetch_page(session, page)          # ~18s per page
                total_pages = body["total_pages"]
                new = save_trades(body["trades"])         # turant DB me save
                STATE.update(page=page, total_pages=total_pages)
                publish("trades", {"trades": new, "state": snapshot()})   # browser ko push
                page += 1
        STATE.update(status="complete", finished_at=time.time())
    except Exception as e:
        STATE.update(status="failed", error=str(e) or type(e).__name__, finished_at=time.time())
    publish("status", snapshot())
    connection.close()                                    # thread ka DB connection band


def start_pull():
    """Return (job_id, already_running)."""
    with _start_lock:
        if STATE["status"] == "running":
            return STATE["job_id"], True
        job_id = uuid.uuid4().hex[:8]
        STATE.update(status="running", job_id=job_id)     # double-start se bachne ke liye
        threading.Thread(target=run_pull, args=(job_id,), daemon=True).start()
        return job_id, False
