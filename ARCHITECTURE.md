# Architecture Note

## Problem
- Full BSE pull = up to 15 min, par network 30s se zyada open HTTP connection kill kar deta hai.
- Dashboard instantly khule, pull ke beech bhi data dikhe, naye trades bina refresh/polling/cron ke aayen.

## Diagram
```
 Browser (dashboard.html)
   |  (1) GET /api/trades        -> DB se instant              [short request]
   |  (2) EventSource /api/stream <---- server push            [25s, phir auto-reconnect]
   |  (3) POST /api/pull         -> 202 + job_id               [short request]
   v
 Django Dashboard (:8000) --- background thread ---> Mock BSE Django (:8001)
   |      page 1..N, har call ~18s (< 30s)             GET /getTrades?page=N
   |  har page ke baad:
   |    - Trade.objects.get_or_create (trade_id UNIQUE)
   |    - event publish -> SSE se browser ko push
   v
 SQLite (Trade table)  <-- dashboard yahin se padhta hai
```

## Design aur kyun
1. **Pull ko request se decouple kiya.** `POST /api/pull` turant 202 deta hai; asli kaam background thread me. Koi connection 15 min open nahi rehta.
2. **Upstream paginated.** Mock BSE total delay ko pages me baant deta hai (har page <= 25s) aur `requests` read timeout 28s hai => 30s limit kabhi cross nahi hoti.
3. **DB = source of truth.** Har page turant save hota hai, isliye dashboard instantly khulta hai aur pull ke dauran bhi partial data dikhta hai.
4. **Push, polling nahi.** SSE (one-way push ke liye WebSocket se simple, Django me Channels bhi nahi chahiye). Network 30s pe connection kill karta hai, isliye server stream ~25s pe khud band karta hai; browser `EventSource` auto-reconnect karta hai aur `Last-Event-ID` se missed events replay hote hain. Server data aane par hi bhejta hai, client baar-baar poochta nahi.
5. **Idempotent.** `trade_id` unique + `get_or_create`: dobara pull par duplicates nahi. Client side bhi `trade_id` se dedupe.
6. **Failure handling.** Har page 3 retries (exponential backoff); fail hone par status `failed` UI me dikhta hai. Ek time par ek hi pull.
7. **No scheduler/cron.** Pull sirf server start par ya button click se trigger hota hai.

## Production me kya badlega
SQLite -> PostgreSQL, in-memory events -> Redis pub/sub, thread -> Celery worker (restart-safe, last page se resume), runserver -> gunicorn/ASGI (uvicorn).
