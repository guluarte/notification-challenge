# Notification Challenge

This repository contains the initial project scaffold for a notification challenge.

The current implementation covers project setup only:

- A FastAPI backend scaffold in `backend/`
- A React + Vite frontend scaffold in `frontend/`
- Planning notes collected under `docs/planning/`
- Local and Docker-oriented example environment files
- Basic tooling for typing, linting, and formatting

The notification workflow itself is not implemented yet. At the moment, the backend exposes a health endpoint and the frontend renders a setup landing page that documents the intended categories and channels.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic Settings
- Frontend: React, Vite
- Python tooling: `uv`, `pyright`, `ruff`, `pytest`
- Frontend tooling: TypeScript checking for JS files, Biome, Vite

## Repository Layout

```text
.
├── backend/
│   ├── alembic.ini
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routes/
│   │   │           └── health.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── main.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   │   └── dtos/
│   │   ├── seeders/
│   │   ├── services/
│   │   └── strategies/
│   │       └── channels/
│   ├── db/
│   │   └── seed.sql
│   ├── migrations/
│   ├── tests/
│   ├── .env.example
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── main.jsx
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles.css
│   ├── .env.example
│   ├── biome.json
│   └── package.json
└── REQUERIMENTS.md
```

## What Exists Today

### Backend

- FastAPI application bootstrap in `backend/app/main.py`
- Centralized settings loading from environment variables in `backend/app/core/config.py`
- Versioned API router assembly in `backend/app/api/v1/router.py`
- Health check route at `GET /v1/health`
- SQLAlchemy model metadata for the normalized notification domain
- Alembic configuration and migrations for both the bootstrap seed table and the normalized domain schema
- Database seed SQL for catalogs, users, and preference mappings in `backend/db/seed.sql`

## Database Diagram

The repository now includes both the original bootstrap seed table and the normalized schema needed for categories, channels, user preferences, submitted messages, and delivery audit records.

```mermaid
erDiagram
    notification_categories {
        VARCHAR code PK
        VARCHAR name UK
        TIMESTAMPTZ created_at
    }
    notification_channels {
        VARCHAR code PK
        VARCHAR name UK
        TIMESTAMPTZ created_at
    }
    users {
        INTEGER id PK
        VARCHAR name
        VARCHAR email UK
        VARCHAR phone_number
        TIMESTAMPTZ created_at
    }
    user_category_subscriptions {
        INTEGER user_id PK, FK
        VARCHAR category_code PK, FK
        TIMESTAMPTZ created_at
    }
    user_channel_preferences {
        INTEGER user_id PK, FK
        VARCHAR channel_code PK, FK
        TIMESTAMPTZ created_at
    }
    messages {
        INTEGER id PK
        VARCHAR category_code FK
        TEXT body
        TIMESTAMPTZ created_at
    }
    notification_deliveries {
        INTEGER id PK
        INTEGER message_id FK
        INTEGER user_id FK
        VARCHAR channel_code FK
        VARCHAR category_code FK
        TEXT message_body
        JSONB recipient_snapshot
        INTEGER attempt_number
        VARCHAR status
        TIMESTAMPTZ attempted_at
        TIMESTAMPTZ delivered_at
    }
    seed_users {
        INTEGER id PK
        TEXT name
        TEXT email UK
        TEXT phone_number
        JSONB categories
        JSONB channels
        TIMESTAMPTZ created_at
    }

    notification_categories ||--o{ user_category_subscriptions : categorizes
    users ||--o{ user_category_subscriptions : subscribes
    notification_channels ||--o{ user_channel_preferences : enables
    users ||--o{ user_channel_preferences : prefers
    notification_categories ||--o{ messages : classifies
    messages ||--o{ notification_deliveries : fan_out
    users ||--o{ notification_deliveries : receives
    notification_channels ||--o{ notification_deliveries : delivers
    notification_categories ||--o{ notification_deliveries : audits
```

### Frontend

- React + Vite application scaffold
- Config-driven app title and backend base URL
- Placeholder UI describing:
  - Message categories: `Sports`, `Finance`, `Movies`
  - Notification channels: `SMS`, `E-Mail`, `Push Notification`

## Prerequisites

- Python `3.12+`
- Node.js `24.14.1` LTS
- `pnpm`
- `uv`
- Docker with the Compose plugin

## Local Setup

### 1. Clone and enter the repository

```bash
git clone <your-repo-url>
cd <repo-directory>
```

### 2. Configure backend environment variables

```bash
cp backend/.env.example backend/.env
```

Current backend variables:

| Variable | Purpose | Example |
| --- | --- | --- |
| `APP_NAME` | FastAPI application title | `Notification API` |
| `APP_ENV` | Runtime environment label | `development` |
| `API_PREFIX` | Shared prefix for API routes | `/v1` |
| `APP_HOST` | Backend bind host | `0.0.0.0` |
| `APP_PORT` | Backend bind port | `8000` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/notifications` |
| `FRONTEND_APP_URL` | Frontend origin | `http://localhost:5173` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `POSTGRES_DB` | Placeholder database name for local/Docker setup | `notifications` |
| `POSTGRES_USER` | Placeholder database user | `postgres` |
| `POSTGRES_PASSWORD` | Placeholder database password | `postgres` |

### 3. Configure frontend environment variables

```bash
cp frontend/.env.example frontend/.env
```

Current frontend variables:

| Variable | Purpose | Example |
| --- | --- | --- |
| `VITE_APP_NAME` | UI title shown in the page | `Notification Console` |
| `VITE_API_BASE_URL` | Backend base URL displayed in the setup UI | `http://localhost:8000/v1` |

## Running the Project Locally

### Backend

Install dependencies:

```bash
cd backend
uv sync --group dev
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Seed the bootstrap data:

```bash
PGPASSWORD="$POSTGRES_PASSWORD" \
psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f db/seed.sql
```

Start the API server:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The current backend health endpoint is:

```text
GET http://localhost:8000/v1/health
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

### Frontend

Install dependencies:

```bash
cd frontend
pnpm install --frozen-lockfile
```

Start the development server:

```bash
pnpm dev
```

The frontend runs at:

```text
http://localhost:5173
```

## Verification Commands

### Backend

Install dependencies first with `uv sync --group dev`, then run:

```bash
cd backend
uv run pyright app/core/config.py app/main.py app/api/v1/router.py app/api/v1/routes/health.py
uv run ruff check app/core/config.py app/main.py app/api/v1/router.py app/api/v1/routes/health.py
```

### Frontend

```bash
cd frontend
pnpm test
pnpm typecheck
pnpm lint
pnpm format:check
pnpm build
```

## Docker Notes

The repository includes a Docker development stack that reuses the same per-service `.env` files used for local development:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docker-compose.yml`

The compose stack starts five services:

- `db`: PostgreSQL 16 with a persistent named volume
- `migrate`: one-shot Alembic job that runs `alembic upgrade head`
- `seed`: one-shot Postgres job that runs `psql -f backend/db/seed.sql`
- `backend`: FastAPI served on port `8000`
- `frontend`: static assets built with Vite and served by Nginx on port `5173`

All API routes are expected to live under the `/v1` prefix.

To start the stack:

```bash
docker compose up --build
```

Before running Docker, create the same service env files used for local development:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The backend, migrate, and seed services read `backend/.env`. Compose overrides only `DATABASE_URL` for the Python services so they point at the `db` service inside Docker. The frontend build reads `frontend/.env`, so the same Vite variables are used for both local development and the Docker image build.

Frontend `VITE_*` values are baked into the image during the build stage, so changing `frontend/.env` requires rebuilding the frontend image.

Schema changes run through Alembic, and seed data runs as a separate `psql` step. A clean reset still uses `docker compose down --volumes`, but reseeding no longer depends on Postgres entrypoint hooks.

All three containers expose Docker healthchecks:

- `db`: PostgreSQL readiness via `pg_isready`
- `backend`: FastAPI readiness via `GET /v1/health`
- `frontend`: Nginx readiness via `GET /health`

## Current Gaps

The following challenge requirements are not implemented yet:

- Message submission endpoint
- Notification orchestration
- Channel strategies
- Delivery logs
- Submission form and log history UI
- Automated tests beyond the empty test package scaffold

## Tradeoffs and Future Scalability

This scaffold intentionally stops early and optimizes for a clean starting point rather than feature completeness.

Current tradeoffs:

- The backend now includes the normalized database schema and ORM metadata, but the API layer still does not use those tables yet.
- The frontend is a placeholder shell instead of a partial implementation of the submission form. This avoids early UI churn before the API contract and persistence model exist.
- The seed flow pre-populates catalogs and user preferences, but there is still no runtime notification dispatch, message intake, or audit log retrieval.

Expected next architectural steps:

- Introduce repositories, services, DTOs, and channel strategies behind clear boundaries
- Connect message submission routes and notification orchestration to the new schema
- Expand the frontend from the setup page into the required submission form and audit log view
- Add automated tests for the schema-backed notification flow and failure isolation behavior
