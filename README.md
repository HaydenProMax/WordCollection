# enCollect

enCollect is a personal English lookup web app. It explains English words, phrases, and sentences with an LLM, displays a fixed-format result, and stores lookup history in PostgreSQL.

## Stack

- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Frontend: plain HTML/CSS/JavaScript
- LLM provider: OpenAI first, with a provider abstraction for future models

## Development Environment

Development is intended to run from WSL on Windows.

The development database uses Docker through `docker-compose.dev.yml`.

Production does not use Docker for the database. Production should connect to a native Linux PostgreSQL service or a managed PostgreSQL database through `DATABASE_URL`.

## Setup

From WSL:

```bash
cd /mnt/d/enCollect
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d db
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Environment Variables

```text
APP_ENV=development
DATABASE_URL=postgresql+psycopg://encollect:encollect_dev_password@localhost:55432/encollect
MODEL_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
```

`OPENAI_API_KEY` is required for real lookups.

## Verified Local Startup Commands

These commands were verified during local testing. Do not change this startup flow casually; update it only when the project structure or runtime requirements truly change.

From WSL:

```bash
cd /mnt/d/enCollect
docker compose -f docker-compose.dev.yml up -d db
docker compose -f docker-compose.dev.yml ps
```

Then:

```bash
cd /mnt/d/enCollect/backend
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

For an OpenAI-compatible proxy, set `OPENAI_BASE_URL` to the API root that contains the `/responses` endpoint. For example:

```text
OPENAI_MODEL=gpt-5.5
OPENAI_BASE_URL=https://www.fhl.mom/v1
OPENAI_API_KEY=your_api_key
```

## Git Flow

- `main`: stable branch
- `dev`: active development branch
- `feature/*`: focused feature branches

Merge tested changes from `dev` into `main`.

## Tests

From `backend/`:

```bash
pytest
```

## Production Deployment

Ubuntu 24.04 deployment instructions are documented in:

```text
docs/ubuntu-24.04-deployment.md
```
