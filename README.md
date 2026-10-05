# BSE Trades Pull & Live Dashboard

A Django-based BSE trades dashboard that fetches trades from a mock BSE API and displays them in real time using **Server-Sent Events (SSE)**.

The dashboard is designed around the following requirements:

- Dashboard opens immediately and displays already available trades.
- A background pull fetches new trades from the mock BSE API.
- Newly fetched trades appear automatically without refreshing the page.
- No client-side polling loop is used.
- No cron job or external scheduler is required.
- Each SSE HTTP connection is kept below 30 seconds.
- The pull delay is configurable, making the complete flow easy to demonstrate.

---

## Architecture Overview

The application consists of two Django services:

```text
                 ┌──────────────────────────┐
                 │       Web Browser         │
                 │   Django Dashboard UI     │
                 └────────────┬─────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │       Dashboard          │
                 │      Django :8000        │
                 │                           │
                 │  REST APIs + SSE Stream   │
                 └────────────┬─────────────┘
                              │
                              │ HTTP
                              ▼
                 ┌──────────────────────────┐
                 │       Mock BSE API       │
                 │      Django :8001        │
                 │                           │
                 │ GET /getTrades?page=N    │
                 └──────────────────────────┘
                              │
                              ▼
                       Seeded trade data
```

The dashboard stores pulled trades in SQLite and pushes newly fetched trades to connected browsers through SSE.

For implementation details, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Technology Stack

- **Python 3.10+**
- **Django 5**
- **Requests**
- **SQLite**
- **Server-Sent Events (SSE)**
- **Vanilla JavaScript**
- **Docker / Docker Compose** for containerized execution

The implementation does not require Celery, Redis, Django Channels, or an external scheduler.

---

# Getting Started

## Prerequisites

Make sure the following are installed:

- Python 3.10+
- Git
- Docker Desktop (only required for the Docker setup)

---

## Option 1 — Run Without Docker

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

**Linux / macOS:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

---

## Start the Application

The application uses two Django processes.

### Terminal 1 — Mock BSE API

The mock BSE service runs on port `8001`.

**Linux / macOS:**

```bash
PULL_DELAY_SECONDS=900 python manage.py runserver 8001 --noreload --settings=config.mock_settings
```

**Windows PowerShell:**

```powershell
$env:PULL_DELAY_SECONDS="900"
python manage.py runserver 8001 --noreload --settings=config.mock_settings
```

### Terminal 2 — Dashboard

The dashboard runs on port `8000`.

```bash
python manage.py runserver 8000 --noreload
```

Open the dashboard:

**http://localhost:8000**

The dashboard automatically starts a pull shortly after startup when `AUTO_PULL_ON_START=true`.

> `--noreload` is recommended because Django's development auto-reloader can execute startup logic more than once, which may trigger duplicate pulls during development.

---

# Quick Demo

For a faster demonstration, use a 2-minute pull delay instead of the default 15 minutes.

### Windows PowerShell

```powershell
$env:PULL_DELAY_SECONDS="120"
python manage.py runserver 8001 --noreload --settings=config.mock_settings
```

Then start the dashboard in the second terminal:

```powershell
python manage.py runserver 8000 --noreload
```

Open:

```text
http://localhost:8000
```

### Expected behavior

1. The dashboard opens immediately.
2. Existing trades are displayed from the database.
3. A **Pull in progress** indicator shows the current progress.
4. New trades appear automatically while the pull is running.
5. New rows are highlighted with a green visual effect.
6. The progress indicator updates as trades are received.
7. When the pull finishes, the status changes to **Up to date**.
8. Refreshing the page loads the persisted trades from SQLite.

No manual page refresh is required during the pull.

---

# Docker Setup

Docker Compose can be used to run the application in a containerized environment.

### Build and start

```bash
docker compose up --build
```

### Fast demo

```bash
PULL_DELAY_SECONDS=120 docker compose up --build
```

On Windows PowerShell, if environment-variable syntax causes issues, set it first:

```powershell
$env:PULL_DELAY_SECONDS="120"
docker compose up --build
```

---

# Configuration

The application can be configured through environment variables.

| Variable | Default | Description |
|---|---:|---|
| `PULL_DELAY_SECONDS` | `900` | Duration of the mock BSE pull |
| `TOTAL_TRADES` | `3000` | Number of seeded trade records |
| `PAGE_SIZE` | `60` | Maximum records returned per API page |
| `BSE_URL` | `http://localhost:8001` | Mock BSE API URL used by the dashboard |
| `AUTO_PULL_ON_START` | `true` | Automatically trigger a pull when the dashboard starts |
| `DB_PATH` | `data/db.sqlite3` | SQLite database location |

For development/demo purposes, `PULL_DELAY_SECONDS=120` is recommended.

---

# API Endpoints

## Mock BSE API — Port 8001

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/getTrades?page=N` | Returns a page of mock trade records |
| `GET` | `/` | Mock BSE service information |

## Dashboard — Port 8000

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/pull` | Starts a new pull |
| `GET` | `/api/trades` | Returns stored trades |
| `GET` | `/api/status` | Returns current pull/status information |
| `GET` | `/api/stream` | SSE endpoint for live trade updates |
| `POST` | `/api/reset` | Resets stored data for demonstration |

---

# Real-Time Update Mechanism

The dashboard uses **Server-Sent Events (SSE)** to deliver newly fetched trades to the browser.

The flow is:

```text
Mock BSE API
      │
      │ paginated trade data
      ▼
Background pull
      │
      ├── Save trades to SQLite
      │
      └── Publish new trade events
                    │
                    ▼
              SSE endpoint
                    │
                    ▼
                Browser
                    │
                    ▼
             Update UI instantly
```

This avoids a client-side polling loop and allows the dashboard to remain responsive while the pull is running.

Each SSE connection is short-lived and stays within the required HTTP connection duration.

---

# Project Structure

```text
bse-django/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── mock_settings.py
│   └── mock_urls.py
│
├── mock_bse/
│   └── ...
│
├── trades/
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   └── templates/
│       └── ...
│
├── data/
│   └── db.sqlite3
│
├── ARCHITECTURE.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

### Main responsibilities

**`mock_bse/`**

Provides the mock BSE API and paginated trade data.

**`trades/`**

Contains the trade model, pull logic, event handling, API views, and dashboard UI.

**`config/`**

Contains Django configuration, URLs, and the separate mock-BSE settings.

**`ARCHITECTURE.md`**

Contains the architecture diagram and design decisions.

---

# Development Notes

### Why SSE?

SSE provides a simple server-to-browser streaming mechanism for one-way live updates. The browser receives new trades as they become available without repeatedly requesting the server.

### Why SQLite?

SQLite keeps the assessment setup simple and self-contained while providing persistence across page refreshes.

### Why no Celery / Redis?

The assessment can be implemented without introducing additional infrastructure. The current design keeps the application lightweight and allows it to run with the Django development server.

### Why `--noreload`?

The application performs startup behavior such as triggering a pull. Django's development auto-reloader can start application code more than once, so `--noreload` avoids duplicate startup execution during development.

---

# Demo / Reset

For another demonstration cycle:

1. Open the dashboard.
2. Use **Reset DB** to clear the stored trades.
3. Start a new pull.
4. Observe the progress indicator.
5. Watch newly fetched trades appear without refreshing the page.
6. Wait for the pull to complete.
7. Refresh the page and verify that the trades remain available from the database.

---

# Submission Checklist

Before submitting the repository, verify:

- [ ] Application starts successfully without Docker.
- [ ] Mock BSE API starts on port `8001`.
- [ ] Dashboard starts on port `8000`.
- [ ] Existing trades appear immediately.
- [ ] Pull can run in the background.
- [ ] New trades appear without page refresh.
- [ ] No client-side polling loop is required.
- [ ] SSE connection works correctly.
- [ ] SQLite persistence works after refresh.
- [ ] Docker Compose starts successfully.
- [ ] `requirements.txt` is up to date.
- [ ] `.env` and virtual-environment files are not committed.
- [ ] `ARCHITECTURE.md` is included.
- [ ] README setup instructions have been tested from a clean environment.

---

## License

This project was developed as part of a Software Engineer technical assessment.
