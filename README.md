# AdCleaner — Telegram Advertisement Detection Bot

A focused Telegram bot that automatically detects and deletes unauthorized advertisements in groups and supergroups.

## Features

- Automatic detection of promotional content using a rule-based scoring engine
- Three protection modes: Relaxed, Normal, Strict
- Whitelist support for trusted users, bots, Telegram chats, and domains
- Detection of Telegram invite links, external URLs, referral links, and advertising phrases
- Handles text messages, captions, edited messages, forwarded posts, and spaced telegram links
- Administrator bypass — admins are never filtered
- Private notification of deletions via inline keyboard controls (optional)
- Deletion logs with automatic expiry (default: 24 hours)
- Per-group configuration (enable/disable, mode, allowlist)
- Docker Compose deployment

## Non-features

This bot is intentionally focused. It does **not** include:
- Automatic bans, mutes, or user restrictions
- CAPTCHA, welcome messages, or member verification
- Profanity, political, or NSFW filtering
- AI/ML moderation or external API calls
- OCR or image recognition
- Redis, Celery, or microservices
- Payment systems or premium plans
- General-purpose anti-spam beyond advertisements

## Technology Stack

| Component | Technology |
|---|---|---|
| Bot framework | Aiogram 3.x (Python 3.9+) |
| Admin API | FastAPI (Python 3.11) |
| Admin frontend | React + TypeScript + Vite + Tailwind |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x (async) |
| Driver | Asyncpg |
| Migrations | Alembic |
| Configuration | Pydantic Settings |
| AI providers | OpenAI / Ollama (optional) |
| Containerization | Docker + Docker Compose |
| Testing | Pytest + pytest-asyncio |
| Linting / Formatting | Ruff |

## BotFather Setup

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot` and follow the prompts to create a new bot.
3. Save the bot token (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).
4. Set bot commands by sending:
   ```
   /setcommands
   ```
   Group commands (`BotCommandScopeAllGroupChats`):
   ```
   on - Enable advertisement protection
   off - Disable advertisement protection
   mode - Change protection mode
   allow - Allow a user, bot, chat, or domain
   removeallow - Remove an allowed entity
   allowlist - Show allowed entities
   status - Show moderation status
   recent - Show recent deletions
   deletedata - Delete group data
   help - Show help
   ```
   Private commands (`BotCommandScopeDefault`):
   ```
   start - Start the bot
   help - Show help
   privacy - Privacy information
   status - Show moderation status
   ```
5. Ensure "Group Privacy" is disabled in BotFather settings (otherwise the bot won't see all messages):
   - Send `/setprivacy` to BotFather
   - Select your bot
   - Choose **Disable**

## Telegram Administrator Permission Requirements

The bot requests only the permission it needs:

- **Delete messages** — required for removing advertisements

It does **not** require permissions to ban, restrict, invite, pin, or change group info.

## Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd reklamatozalovchi
   ```

2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set your bot token:
   ```
   BOT_TOKEN=your_bot_token_here
   ```

   Adjust other settings as needed:
   ```
   DEFAULT_MODE=normal
   DELETION_LOG_RETENTION_HOURS=24
   CLEANUP_INTERVAL_MINUTES=30
   MESSAGE_EXCERPT_MAX_LENGTH=250
   ```

## Local Docker Deployment

```bash
docker compose up --build -d
```

This starts four services:
- `postgres` — PostgreSQL 16 database with persistent storage
- `bot` — AdCleaner bot (aiogram, Python)
- `api` — SecAdmin REST API (FastAPI, Python)
- `web` — Admin web dashboard (nginx + React)

The bot will:
1. Wait for PostgreSQL to become healthy
2. Run database migrations
3. Start polling for Telegram updates

After first start, set up database roles and seed an admin officer:

```bash
docker compose exec -T postgres psql -U adcleaner adcleaner < scripts/create_roles.sql
docker compose exec bot python scripts/seed_officer.py --telegram-id YOUR_TELEGRAM_ID
```

Then open `http://localhost` to access the admin dashboard.

To stop:
```bash
docker compose down
```

## Database Migrations

Migrations run automatically on startup via the entrypoint script.

Manual migration commands:
```bash
# Run migrations
docker compose exec bot alembic upgrade head

# Create a new migration (auto-detect changes)
docker compose exec bot alembic revision --autogenerate -m "description"

# Rollback one step
docker compose exec bot alembic downgrade -1
```

## Development Commands

```bash
# Install locally (requires Python 3.9+)
pip install -e ".[dev]"

# Run the bot locally
python -m app.main

# Lint
ruff check app/

# Format
ruff format app/

# Type check (if pyright or mypy is available)
# pyright app/
```

## Test Commands

```bash
# Run all tests (128+ tests)
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_ai_providers.py
```

## Project Structure

```
adcleaner/
├── app/                            # Bot core (Python)
│   ├── main.py                     # Entry point
│   ├── config.py                   # Pydantic Settings
│   ├── bot/                        # Bot framework wiring
│   ├── handlers/                   # Telegram message handlers
│   ├── detector/                   # Content detection engine
│   ├── database/                   # SQLAlchemy models, repositories
│   ├── services/                   # Moderation, allowlist, enforcement
│   ├── secadmin/                   # Outbox worker (background processing)
│   ├── ai/                         # AI provider abstraction (OpenAI/Ollama)
│   ├── i18n/                       # Internationalization (Uzbek)
│   └── core/                       # Logging, utilities
│
├── api/                            # SecAdmin REST API (FastAPI, Python)
│   ├── main.py                     # FastAPI app setup
│   ├── config.py                   # API-specific settings
│   ├── auth/                       # JWT authentication
│   ├── routers/                    # Route modules (events, cases, etc.)
│   ├── schemas/                    # Pydantic request/response schemas
│   └── deps.py                     # Dependency injection
│
├── web/                            # Admin dashboard (React + Vite)
│   ├── src/
│   │   ├── pages/                  # Dashboard, Events, Cases, etc.
│   │   ├── components/             # Layout, shared components
│   │   ├── api/                    # HTTP client, API queries
│   │   ├── stores/                 # React context (auth)
│   │   └── hooks/                  # Custom hooks
│   ├── Dockerfile.web              # Nginx production build
│   └── package.json
│
├── migrations/                     # Alembic migrations
│   ├── env.py                      # Async migration environment
│   └── versions/
│       ├── 0001_initial.py         # Public schema (bot core)
│       └── 0003_secadmin.py        # SecAdmin schema (all security tables)
│
├── tests/
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
│
├── scripts/
│   ├── create_roles.sql            # PostgreSQL role setup
│   └── seed_officer.py            # Seed first admin user
│
├── Dockerfile                      # Bot image (Python 3.9)
├── Dockerfile.api                  # API image (Python 3.11)
├── Dockerfile.web                  # Web image (node build + nginx)
├── docker-compose.yml              # All 4 services
├── .env.example
├── pyproject.toml
├── DEPLOYMENT.md                   # Full deployment guide
└── README.md
```

## Bot Commands

| Command | Scope | Description |
|---|---|---|
| `/start` | Private | Bot introduction, add-to-group button |
| `/help` | Both | Show available commands |
| `/privacy` | Private | Privacy information |
| `/on` | Group | Enable advertisement protection |
| `/off` | Group | Disable advertisement protection |
| `/mode` | Group | Change protection mode (Relaxed/Normal/Strict) |
| `/allow` | Group | Allow a user, bot, chat, or domain |
| `/removeallow` | Group | Remove an allowed entity |
| `/allowlist` | Group | Show allowed entities |
| `/status` | Both | Show moderation status |
| `/recent` | Group | Show recent deletions |
| `/deletedata` | Group | Delete all group data (owner only) |

All group commands require administrator privileges.

## Detection Scoring

The bot uses a deterministic rule-based scoring engine with these signals:

**Strong signals** (+5 or +6):
- External Telegram invite link: +6
- "Join" or "subscribe" near Telegram link: +4
- Referral/affiliate parameter: +4
- Repeated promotional message: +5
- Unauthorized bot promotion: +5
- Strong advertising phrase: +3
- Offer combined with contact request: +3

**Medium signals** (+2):
- External website URL
- Multiple links or usernames
- Price or discount language
- Forwarded post from unrelated channel
- URL combined with commercial phrase: +2

**Thresholds:**
- Relaxed: 9 (only clear ads)
- Normal: 6 (default, balanced)
- Strict: 4 (most promotional links)

## Privacy

- Messages are read only to detect advertisements
- Normal messages are never permanently stored
- Only deleted message metadata is stored (score, reasons, short excerpt)
- Deletion logs expire automatically (default: 24 hours)
- Message contents are never sent to third-party services
- Users are not tracked across unrelated groups
- Data is not sold or shared
- Group owners can delete all data via `/deletedata`

## Telegram Limitations

- Image text cannot be detected without OCR
- QR codes inside images are not analyzed
- Encrypted content cannot be inspected
- The bot only receives updates while active (messages sent before adding the bot are not seen)
- Some service messages cannot be deleted
- Rule-based filtering may produce occasional false positives or negatives
- The bot may not receive messages from other bots depending on Telegram API behavior
- Private warnings cannot be sent to users who have not started the bot or have blocked it

## Troubleshooting

**Bot does not respond to commands:**
- Ensure the bot is an administrator in the group
- Ensure the bot has the "Delete messages" permission
- Check the bot token in `.env`

**Bot cannot see messages:**
- Ensure "Group Privacy" is disabled in BotFather settings
- The bot must be an administrator

**Bot crashes on startup:**
- Check `docker compose logs bot` for errors
- Ensure PostgreSQL is running: `docker compose ps`
- Verify database URL in `.env`

**Tests fail:**
- Install aiosqlite: `pip install aiosqlite`
- Run tests: `pytest tests/`

## Production Deployment Notes

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment guide covering all four services.

- Set a strong `POSTGRES_PASSWORD` and `API_SECRET_KEY` in `.env`
- Run `scripts/create_roles.sql` after first deploy to set up database roles
- Seed an admin officer via `scripts/seed_officer.py`
- Do not expose PostgreSQL ports publicly unless required
- Use HTTPS for the web dashboard in production
- Monitor logs with `docker compose logs -f bot` and `docker compose logs -f api`
- Database backups should cover the `pgdata` volume
- The in-memory detection cache is lost on restart (by design)
- For Telegram API rate limits, aiogram handles retries automatically

## Adding a Bot to a Group

1. Open the bot's private chat and use the "Add to group" button, or search for the bot's username in Telegram and add it to your group.
2. Promote the bot to administrator with at least the "Delete messages" permission.
3. The bot will confirm activation automatically.
4. Use `/mode` to adjust the protection level if needed.
