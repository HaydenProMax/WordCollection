# enCollect Development Plan

Last updated: 2026-05-10

## Project Summary

enCollect is a personal English lookup web app. A user enters an English word, phrase, or sentence, the app asks an LLM for a fixed-format explanation, displays the result, and stores the lookup in a database for later review.

## Confirmed Scope

- Personal use only.
- Local development on Windows + WSL.
- Local development database runs in Docker through `docker-compose.dev.yml`.
- Production database runs as a normal PostgreSQL service on Linux, not in Docker and not through Compose.
- Git-managed development flow.
- All active development happens on `dev`.
- Tested changes are merged into `main`.
- First LLM provider is OpenAI.
- Provider layer must allow future model providers.
- Stored lookup fields:
  - Original text
  - Pronunciation
  - Explanation
  - Example sentences
- No review/reminder system in the first versions.

## Branch Strategy

| Branch | Purpose | Merge Rule |
|---|---|---|
| `main` | Stable release branch | Only receives tested changes from `dev` |
| `dev` | Active integration branch | Receives completed feature branches |
| `feature/*` | Isolated feature work | Merge into `dev` after local tests |

## Version Roadmap

### v0.1.0 - Core Lookup MVP

Status: In progress

Goal: Complete the core personal lookup workflow.

Required features:

- [x] FastAPI backend scaffold
- [x] PostgreSQL development database via `docker-compose.dev.yml`
- [x] SQLAlchemy database connection
- [x] Alembic migrations
- [x] Lookup table
- [x] OpenAI provider abstraction
- [x] Fixed JSON explanation schema
- [x] `POST /api/lookups`
- [x] `GET /api/lookups`
- [x] `GET /api/lookups/{id}`
- [x] Frontend lookup form
- [x] Frontend fixed-format result display
- [x] Frontend history list
- [x] Basic API tests
- [x] README startup instructions

Acceptance criteria:

- [x] App starts from WSL.
- [x] Local Docker PostgreSQL is reachable.
- [x] Database migrations run from an empty database.
- [x] A word lookup returns original text, pronunciation, explanation, and examples.
- [x] A sentence lookup returns original text, explanation, and examples.
- [x] Successful lookups are persisted.
- [x] History survives page refresh.
- [ ] Missing OpenAI API key produces a clear error.
- [x] Tests pass on `dev`.
- [x] `dev` is merged into `main`.
- [x] Release tag `v0.1.0` is created.

### v0.2.0 - History Management

Status: Released

Goal: Make saved lookups easier to manage.

Candidate features:

- [x] Search history
- [x] Delete lookup
- [x] Regenerate explanation
- [x] Update lookup explanation after regeneration
- [x] Better empty/error/loading states

### v0.3.0 - Usability Polish

Status: In progress

Goal: Improve daily-use ergonomics before adding heavier organization features.

Candidate features:

- [x] Copy explanation
- [x] Filter history by query type
- [x] Better delete confirmation
- [ ] Better loading states
- [ ] Better empty states

Deferred features:

- [ ] Favorite lookup
- [ ] Tags
- [ ] Basic statistics

Completed business additions:

- [x] Export JSON
- [x] Export CSV

## Technical Decisions

| Area | Decision | Reason | Alternative |
|---|---|---|---|
| Backend | FastAPI | Clear API structure and testability | Python standard library server |
| Database | PostgreSQL | Same class of database for development and production | SQLite |
| Local DB | Docker PostgreSQL | Easy local reset and consistent setup | Native Windows PostgreSQL |
| Production DB | Native Linux PostgreSQL or cloud PostgreSQL | Better fit for real deployment | Dockerized production DB |
| ORM | SQLAlchemy | Mature Python ORM | Raw SQL |
| Migrations | Alembic | Controlled schema evolution | Manual SQL scripts |
| Frontend | Plain HTML/CSS/JS initially | Keeps v0.1 small | React/Vite |
| LLM | Provider abstraction | Future model providers can be added cleanly | Hard-coded OpenAI calls |

## Target Project Structure

```text
enCollect/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   └── openai_provider.py
│   │   └── routers/
│   │       └── lookups.py
│   ├── tests/
│   ├── alembic/
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── docs/
│   └── development-plan.md
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
└── README.md
```

## API Plan

### POST /api/lookups

Creates a lookup by asking the configured LLM provider for an explanation and saving the result.

Request:

```json
{
  "text": "subtle"
}
```

Response:

```json
{
  "id": "string",
  "original": "subtle",
  "queryType": "word",
  "pronunciation": "/ˈsʌtəl/",
  "explanation": "微妙的、不易察觉的...",
  "examples": [
    {
      "english": "There is a subtle difference between the two words.",
      "chinese": "这两个词之间有细微差别。"
    }
  ],
  "createdAt": "2026-05-10T00:00:00Z"
}
```

### GET /api/lookups

Returns recent lookup history.

Planned query params:

- `limit`
- `offset`

### GET /api/lookups/{id}

Returns one saved lookup.

## Database Plan

Primary table: `lookups`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID or BIGSERIAL | Primary key |
| `original` | TEXT | User input |
| `query_type` | VARCHAR | `word`, `phrase`, or `sentence` |
| `pronunciation` | TEXT | Can be empty for sentences |
| `explanation` | TEXT | Chinese explanation |
| `examples` | JSONB | Example sentence objects |
| `model_provider` | VARCHAR | Example: `openai` |
| `model_name` | VARCHAR | Example: `gpt-4.1-mini` |
| `raw_response` | JSONB | Optional debugging payload |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Update time |

## Environment Plan

Development:

```text
APP_ENV=development
DATABASE_URL=postgresql+psycopg://encollect:encollect_dev_password@localhost:55432/encollect
MODEL_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
```

Production:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://encollect:<password>@127.0.0.1:5432/encollect
MODEL_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=<secret>
```

## Test Plan

Unit tests:

- [ ] Query type classification
- [ ] LLM response schema parsing
- [ ] Invalid LLM response handling
- [ ] Lookup model serialization

Integration tests:

- [ ] Create lookup through API
- [ ] List lookup history through API
- [ ] Get lookup detail through API
- [ ] Database write/read round trip

Manual checks:

- [ ] Start Docker PostgreSQL from WSL
- [ ] Run migrations
- [ ] Start backend
- [ ] Open frontend
- [ ] Query a word
- [ ] Query a sentence
- [ ] Refresh page and confirm history remains

## Deployment Plan

Development deployment:

1. Checkout `dev`.
2. Start local development database with `docker compose -f docker-compose.dev.yml up -d db`.
3. Run migrations.
4. Start backend from WSL.
5. Open the local web app in Windows browser.

Production deployment:

1. Merge tested `dev` into `main`.
2. Pull `main` on Linux server.
3. Install/update Python dependencies.
4. Configure production environment variables.
5. Confirm native PostgreSQL is reachable.
6. Run Alembic migrations.
7. Restart application service.
8. Verify lookup and history flows.

Rollback:

1. Stop the new application version.
2. Revert to the previous Git tag or commit.
3. If needed, run Alembic downgrade for the latest migration.
4. Restart service.
5. Verify core lookup flow.

## Progress Log

### 2026-05-10

- Created the initial development plan.
- Confirmed local development uses Docker PostgreSQL.
- Confirmed production uses direct PostgreSQL on Linux, not Docker.
- Confirmed `dev` to `main` release flow.

### 2026-05-10 Development Start

- Started restructuring the prototype into the planned FastAPI project.
- Added backend, frontend, Alembic, and development database scaffolding.
- Renamed the Compose file to `docker-compose.dev.yml` to make clear it is development-only.
- Added API tests with a fake LLM provider.
- Verified `python -m compileall backend`.
- Verified `python -m pytest`.
- Initialized Git repository.
- Created `main` and `dev` branches.
- Committed the MVP scaffold on `dev` as `5caf96c`.

### 2026-05-10 Local Database Integration

- Found existing PostgreSQL containers on ports `5432` and `54329` that belong to other projects.
- Moved enCollect development PostgreSQL to port `55432` to avoid conflicts.
- Started `encollect-dev-db` with `docker-compose.dev.yml`.
- Ran `python -m alembic upgrade head` successfully against PostgreSQL.
- Verified `GET /api/lookups` returns `200` with an empty list.
- Verified missing `OPENAI_API_KEY` returns `502` and does not create a record.
- Verified real PostgreSQL insert/read/delete path with a fake LLM provider.

### 2026-05-10 Model Configuration

- Added `OPENAI_BASE_URL` so OpenAI-compatible proxy endpoints can be used.
- Documented custom model configuration such as `OPENAI_MODEL=gpt-5.5`.
- Verified local `.env` is read correctly with `OPENAI_MODEL=gpt-5.5` and `OPENAI_BASE_URL=https://www.fhl.mom/v1`.
- Verified the configured provider returns a valid structured explanation for `subtle`.

### 2026-05-10 Local Browser Verification

- Verified the full local browser flow at `http://127.0.0.1:8000/`.
- User confirmed local testing passed.
- Confirmed the startup commands below are the current stable local development flow.
- Do not change these commands casually; only update them when the runtime structure changes intentionally.

```bash
cd /mnt/d/enCollect
docker compose -f docker-compose.dev.yml up -d db
docker compose -f docker-compose.dev.yml ps
cd /mnt/d/enCollect/backend
source .venv/bin/activate
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

### 2026-05-10 v0.1.0 Release

- Merged `dev` into `main`.
- Released the first stable local MVP as `v0.1.0`.

### 2026-05-10 v0.2.0 History Management Start

- Added backend history search with `GET /api/lookups?q=...`.
- Added `DELETE /api/lookups/{id}`.
- Added `POST /api/lookups/{id}/regenerate`.
- Added frontend search input, delete action, and regenerate action.
- Expanded API tests from 4 to 7 cases.

### 2026-05-10 v0.2.0 Release

- User verified history search, delete, and regenerate locally in the browser.
- Prepared `v0.2.0` for merge into `main`.

### 2026-05-10 v0.3.0 Replanning

- Replanned `v0.3.0` from organization/export features to usability polish.
- Deferred favorites, tags, export, and statistics until real usage shows they are needed.

### 2026-05-10 v0.3.0 Usability Polish Start

- Added copy explanation action for the currently displayed lookup.
- Added history filtering by query type.
- Replaced browser delete prompt with an in-page second-click confirmation.
- Added API support and tests for `query_type` history filtering.

### 2026-05-10 Data Export

- Added `GET /api/export/json`.
- Added `GET /api/export/csv`.
- Added JSON and CSV export links in the history panel.
- Added API tests for both export formats.
