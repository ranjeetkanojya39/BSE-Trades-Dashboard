# BSE Trades Pull + Live Dashboard (Django)

Mock BSE API (15 min pull) + dashboard jo instantly khulta hai aur pull ke dauran naye trades **push** se live dikhata hai.
No polling, no cronjob/scheduler, har HTTP connection < 30s.

## Stack
Python 3.10+, Django 5, requests, SQLite, Server-Sent Events (SSE), vanilla JS.
(Celery/Redis/Channels ki zarurat nahi: ek `python manage.py runserver` se chalta hai.)

## Setup (bina Docker)
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

Do terminals kholo (dono me venv activate):

**Terminal 1 - Mock BSE (port 8001)**
```bash
# Linux/Mac
PULL_DELAY_SECONDS=900 python manage.py runserver 8001 --noreload --settings=config.mock_settings
# Windows PowerShell
$env:PULL_DELAY_SECONDS=900
python manage.py runserver 8001 --noreload --settings=config.mock_settings
```

**Terminal 2 - Dashboard (port 8000)**
```bash
python manage.py runserver 8000 --noreload
```

Browser: **http://localhost:8000**  (server start hone ke ~3s baad pull apne aap shuru hota hai)

> `PULL_DELAY_SECONDS=120` rakho agar jaldi demo chahiye (2 min). Default 900 = 15 min.
> `--noreload` zaruri hai, warna auto-reloader do baar start karke pull duplicate chala deta hai.

## Setup (Docker)
```bash
docker compose up --build
PULL_DELAY_SECONDS=120 docker compose up --build     # fast demo
```

## Config (env vars)
| Var | Default | Matlab |
|---|---|---|
| `PULL_DELAY_SECONDS` | 900 | Mock BSE ka full pull time |
| `TOTAL_TRADES` | 3000 | Seeded records |
| `PAGE_SIZE` | 60 | Max records per page |
| `BSE_URL` | http://localhost:8001 | Dashboard -> mock BSE |
| `AUTO_PULL_ON_START` | true | Startup pe ek pull trigger |
| `DB_PATH` | data/db.sqlite3 | SQLite file |

## Endpoints
- Mock BSE (8001): `GET /getTrades?page=N`, `GET /` (info)
- Dashboard (8000): `POST /api/pull` (202), `GET /api/trades`, `GET /api/status`, `GET /api/stream` (SSE), `POST /api/reset` (demo)

## Project structure
```
config/        settings, urls (dashboard), mock_urls + mock_settings (mock BSE)
mock_bse/      GET /getTrades (paginated + delay)
trades/        models.py (Trade), services.py (background pull + events), views.py, templates/ (dashboard UI)
```

## Demo kaise dikhaye
1. Dashboard kholo: trades turant dikhte hain, badge "Pull in progress (x/y)".
2. Bina refresh ke naye rows green flash ke saath aate hain, progress bar badhta hai.
3. Pull khatam: badge "Up to date". Page refresh karo: data DB se instantly aata hai.
4. "Reset DB" + "Start new pull" se dobara demo.

Design detail: `ARCHITECTURE.md`
