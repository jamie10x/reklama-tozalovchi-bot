# Project Context — Reklama Tozalovchi Bot

## Architecture

- **Language**: Python 3.9
- **Framework**: aiogram 3.x (Telegram Bot) + FastAPI (web API)
- **Database**: PostgreSQL via SQLAlchemy 2.0 (async)
- **ORM**: SQLAlchemy 2.0 async with `Mapped` / `mapped_column` style
- **Migrations**: Alembic
- **Testing**: pytest + pytest-asyncio
- **Linting**: ruff
- **Project structure**: `app/` (bot core), `api/` (FastAPI), `migrations/`, `tests/`, `scripts/`, `web/` (frontend)

## Key Directories

- `app/database/secadmin_models.py` — All secadmin SQLAlchemy models (Single Table Inheritance for some)
- `app/database/repositories/` — Repository pattern per entity
- `app/services/` — Business logic (moderation, observation, enforcement_bridge, allowlist)
- `app/detector/` — Content detection / extraction pipeline
- `app/ai/` — AI provider abstraction (Ollama, OpenAI)
- `app/handlers/` — Telegram message handlers
- `app/secadmin/` — Background worker for processing outbox messages
- `app/i18n/` — Internationalization (Uzbek)
- `api/routers/` — FastAPI route modules
- `scripts/` — Utility scripts (seed officer, create roles)
- `web/` — React/Vite frontend with Tailwind

## Session State — 2026-06-21

### Changes Made
1. Removed duplicate `__table_args__` from 12 secadmin models — each model had `__table_args__` defined twice (first as bare dict `{"schema": SECADMIN_SCHEMA}`, then as a full tuple that already included the schema). The first definition was dead code.
2. Committed to `develop` and fast-forward merged to `main`.

### Known Non-Issues (PyCharm False Positives)
- `Unresolved reference '__future__'` — PyCharm interpreter issue; stdlib module
- `No module named 'asyncio'` / `'json'` / etc. — PyCharm not using `.venv/` interpreter
- `Class does not define '__or__'` — `from __future__ import annotations` makes `|` valid at runtime on 3.9, but PyCharm doesn't understand it
- `No data sources configured for SQL` — PyCharm doesn't know PostgreSQL

### Current State
- Python venv: `.venv/` at project root
- Python version: 3.9
- All 128 tests pass, ruff clean
- Branch: `main` and `develop` both at `a269ffe`

## Known Patterns
- `cython`: use from `now` utils with `@utcnow` / `from app.core.utils import utcnow`
- `postgresql`: use UUID primary keys with `UUID(as_uuid=True)` and `default=uuid.uuid4`
- `sqlalchemy __table_args__`: must be defined exactly once per model — either as `dict` (simple schema) or `tuple` (constraints + schema as last element), never both
- `migrations`: naming convention `XXXX_description.py`
- `pytest fixtures`: use `conftest.py` with async fixtures and `sessionmaker`
