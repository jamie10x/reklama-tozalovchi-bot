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
- Web dashboard or Telegram Mini App
- Redis, Celery, or microservices
- Payment systems or premium plans
- General-purpose anti-spam beyond advertisements

## Technology Stack

| Component | Technology |
|---|---|
| Runtime | Python 3.9+ |
| Bot framework | Aiogram 3.x |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x (async) |
| Driver | Asyncpg |
| Migrations | Alembic |
| Configuration | Pydantic Settings |
| Containerization | Docker + Docker Compose |
| Testing | Pytest + pytest-asyncio |
| Linting | Ruff |

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
docker compose up --build
```

This starts two services:
- `postgres` — PostgreSQL 16 database with persistent storage
- `bot` — The AdCleaner bot with auto-migration

The bot will:
1. Wait for PostgreSQL to become healthy
2. Run database migrations
3. Start polling for Telegram updates

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
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

## Project Structure

```
adcleaner/
├── app/
│   ├── main.py                    # Application entry point
│   ├── config.py                  # Pydantic Settings
│   ├── logging_config.py          # Structured logging setup
│   │
│   ├── bot/
│   │   ├── commands.py            # BotFather command definitions
│   │   ├── keyboards.py           # Inline keyboard builders
│   │   ├── middlewares.py         # DB session, error handling middlewares
│   │   └── filters.py             # Custom aiogram filters (admin, group, private)
│   │
│   ├── handlers/
│   │   ├── private.py             # Private chat commands
│   │   ├── commands.py            # Group management commands
│   │   ├── messages.py            # New message processing
│   │   ├── edited_messages.py     # Edited message processing
│   │   └── membership.py          # Bot add/remove handling
│   │
│   ├── detector/
│   │   ├── models.py              # DetectionResult dataclass
│   │   ├── normalizer.py          # Text, URL, domain normalization
│   │   ├── extractor.py           # Text/entity extraction
│   │   ├── phrases.py             # Advertising phrase definitions
│   │   ├── scoring.py             # Scoring engine with signals
│   │   └── service.py             # Main detection orchestrator
│   │
│   ├── database/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── session.py             # Async session management
│   │   ├── models.py              # Chat, AllowedEntity, DeletionLog
│   │   └── repositories/
│   │       ├── chats.py           # Chat CRUD operations
│   │       ├── allowlist.py       # Allowlist CRUD operations
│   │       └── deletion_logs.py   # Deletion log CRUD operations
│   │
│   ├── services/
│   │   ├── permissions.py         # Admin/bot permission checks
│   │   ├── moderation.py          # Main moderation flow
│   │   ├── allowlist.py           # Allowlist business logic
│   │   ├── notifications.py       # Admin notification helpers
│   │   └── cleanup.py             # Periodic deletion log cleanup
│   │
│   └── utils/
│       ├── telegram.py            # HTML escape, domain extraction
│       └── time.py                # Time helpers
│
├── migrations/
│   ├── env.py                     # Alembic async environment
│   ├── script.py.mako             # Migration template
│   └── versions/
│       └── 0001_initial.py        # Initial schema migration
│
├── tests/
│   ├── conftest.py                # Shared test fixtures
│   ├── unit/
│   │   ├── test_normalizer.py     # Text/URL normalization tests
│   │   ├── test_extractor.py      # Text/entity extraction tests
│   │   ├── test_scoring.py        # Scoring engine tests
│   │   └── test_detector_service.py # Detection service tests
│   └── integration/
│       ├── conftest.py            # Integration test setup
│       ├── test_chats_repository.py
│       ├── test_allowlist_repository.py
│       └── test_deletion_logs_repository.py
│
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── .env.example
├── pyproject.toml
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

- Set a strong `POSTGRES_PASSWORD` in `.env`
- Do not expose PostgreSQL ports publicly unless required
- Use a reverse proxy if webhooks are implemented in the future
- Monitor logs with `docker compose logs -f bot`
- Database backups should cover the `pgdata` volume
- The in-memory detection cache is lost on restart (by design)
- For Telegram API rate limits, aiogram handles retries automatically

## Adding a Bot to a Group

1. Open the bot's private chat and use the "Add to group" button, or search for the bot's username in Telegram and add it to your group.
2. Promote the bot to administrator with at least the "Delete messages" permission.
3. The bot will confirm activation automatically.
4. Use `/mode` to adjust the protection level if needed.
