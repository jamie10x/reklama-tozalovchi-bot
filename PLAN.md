# SecAdmin Platform — Implementation Plan

---

## 1. Executive Summary

SecAdmin is a private security operations platform layered on top of the existing AdCleaner Telegram bot. The existing bot handles real-time message processing and deletion; SecAdmin adds background AI analysis, threat-indicator correlation, officer review, case management, and audit logging.

The current repository (`reklama-tozalovchi-bot`) has 39 Python source files, 69 passing tests, and a working Docker deployment. Before SecAdmin can be added, **8 confirmed code defects must be repaired** (see section 3).

Total implementation is estimated at **10 phases** with the first 4 being the MVP.

---

## 2. Current Repository Architecture

### File Tree (39 source files)

```
app/
  main.py                          # Entry point, wires routers + middlewares
  config.py                        # Pydantic Settings (12 fields)
  logging_config.py                # Log format setup
  bot/
    commands.py                    # BotCommand registration (private + group)
    filters.py                     # IsGroupMessage, IsPrivateMessage
    keyboards.py                   # Inline keyboards (mode, confirm delete, allowlist)
    middlewares.py                 # DatabaseSessionMiddleware, ErrorLoggingMiddleware
  handlers/
    commands.py                    # 10 group commands + 3 callback handlers
    messages.py                    # handle_group_message (entry point for detection)
    edited_messages.py             # handle_edited_message
    membership.py                  # Bot add/kick/promote handlers
    private.py                     # /start, /help, /privacy in PM
  services/
    moderation.py                  # ModerationService.process_message() — central pipeline
    allowlist.py                   # AllowlistService (add/remove/list entities)
    permissions.py                 # is_user_admin, bot_can_delete_messages, is_group_owner
    cleanup.py                     # Periodic deletion-log cleanup
    notifications.py               # notify_admins — DEAD CODE (never called)
  detector/
    service.py                     # DetectionService.analyze() — detection orchestrator
    scoring.py                     # scoring_pipeline — signal weighting + threshold
    phrases.py                     # AD_PHRASES dict + PhraseMatcher
    normalizer.py                  # Text normalization, domain/username/TG-link extraction
    extractor.py                   # extract_text, extract_urls, extract_mentions
    models.py                      # DetectionResult dataclass
  database/
    base.py                        # SQLAlchemy DeclarativeBase
    session.py                     # Engine, sessionmaker, get_session
    models.py                      # Chat, AllowedEntity, DeletionLog ORM models
    repositories/
      chats.py                     # ChatRepository
      allowlist.py                 # AllowlistRepository
      deletion_logs.py             # DeletionLogRepository
  utils/
    telegram.py                    # escape_html, extract_username_from_mention — DEAD CODE
    time.py                        # utcnow, hours_ago, minutes_ago — DEAD CODE
migrations/
  env.py                           # Alembic async env
  versions/0001_initial.py         # Initial schema
tests/
  unit/                            # 49 tests (extractor, normalizer, scoring, detector)
  integration/                     # 20 tests (repositories with SQLite)
```

### Message Processing Flow

```
Telegram Message
  → router (commands.py / messages.py / edited_messages.py)
    → handler
      → messages.py: handle_group_message()
        1. ChatRepository.get_by_telegram_id()        ← DB query 1
        2. Check chat.enabled
        3. ModerationService.process_message()
          → 3a. ChatRepository.get_by_telegram_id()   ← DB query 2 (DUPLICATE)
          → 3b. Check chat.bot_can_delete_messages
          → 3c. is_user_admin() → get_chat_member()   ← Telegram API call
          → 3d. Allowlist checks (users, bots)
          → 3e. DetectionService.analyze()
            → Scoring pipeline (scoring_pipeline)
          → 3f. If ad: delete_message() → Telegram API
          → 3g. If deleted: DeletionLogRepository.create()
```

### Current Database Models

```
Chats:         id (UUID PK), telegram_chat_id (BIGINT UNIQUE), title, username,
               enabled, mode, owner_user_id, linked_chat_id,
               bot_can_delete_messages, created_at, updated_at, removed_at

AllowedEntity: id (UUID PK), chat_id (FK→chats), entity_type, entity_value,
               telegram_entity_id, display_name, created_by_user_id, created_at

DeletionLog:   id (UUID PK), chat_id (FK→chats, indexed), telegram_message_id,
               sender_user_id, sender_chat_id, sender_is_bot, score, reasons (JSON),
               detected_domains (JSON), detected_telegram_entities (JSON),
               message_excerpt (Text), created_at, expires_at
```

### Current Docker Services

```
postgres:16-alpine       — Health check, persistent volume, restart: unless-stopped
adcleaner-bot            — python:3.11-slim, non-root user, depends on postgres healthy
```

### Test Coverage

- **49 unit tests**: extractor (11), normalizer (12), scoring (15), detector service (11)
- **20 integration tests**: chats repo (9), allowlist repo (7), deletion logs repo (4)
- **Backend**: SQLite via aiosqlite, persistent DB file
- **Missing**: No service-layer tests, no handler tests, no bot tests, no config tests

---

## 3. Confirmed Code Defects

Verified against current `main` at `88a1363`. All defects reference specific file paths and line numbers.

### CRITICAL (Fix Before SecAdmin)

| # | Defect | File | Lines | Impact |
|---|--------|------|-------|--------|
| C1 | **Chat mode never reaches detection** | `app/services/moderation.py:85-95` | `process_message` calls `self._detection.analyze()` without passing `mode`. The `chat.mode` column exists in the DB and is set by `/mode` command, but is never forwarded. `DetectionService.analyze()` defaults to `mode="normal"`. **All chats effectively operate in Normal mode.** | Mode configuration is non-functional |
| C2 | **`sender_id` not passed to detection** | `app/services/moderation.py:85-95` | `process_message()` receives `sender_id` but never passes it to `self._detection.analyze()`. The repeat-promotion bonus (`+5` at `app/detector/service.py:132-139`) requires `sender_id is not None` and **never triggers**. | Repeat-penalty is dead code |
| C3 | **`sender_is_bot` not passed to detection** | `app/services/moderation.py:85-95` | Same as above — `sender_is_bot` parameter exists in `process_message` but isn't forwarded. `DetectionService.analyze()` always gets `sender_is_bot=False`. | Bot detection disabled |
| C4 | **Whitelisted URLs still scored** | `app/detector/service.py:118-130` | Code creates `filtered_urls` (domain-whitelisted) at lines 97-103 and uses it for early-return, but passes the **unfiltered** `list(extracted_urls)` to `scoring_pipeline()`. Same for Telegram usernames. | Allowlist bypasses only prevent early-return, not scoring |
| C5 | **Deletion logs expire immediately** | `app/database/repositories/deletion_logs.py:30-32` | When `expires_at is None`, defaults to `datetime.now(timezone.utc)` — **equal to `created_at`**. Cleanup task deletes them on the next 30-minute cycle. | Deletion logs are never persisted longer than 30 min |
| C6 | **Allowlist by username never matches** | `app/services/moderation.py:72-77` | User allowlist checks `entry.telegram_entity_id == sender_id` or `entry.entity_value == str(sender_id)`. Users added via `/allow @username` have `telegram_entity_id=None` and `entity_value=username`. `str(sender_id) == username` is **never true**. | `/allow @username` is non-functional |
| C7 | **Double membership handler execution** | `app/handlers/membership.py:98-116` | The catch-all `bot_permission_updated` handler fires FOR EVERY `my_chat_member` event, including those already handled by the specific `IS_MEMBER`, `KICKED`, `IS_NOT_MEMBER` handlers. | Duplicate registration, duplicate messages |
| C8 | **`get_by_telegram_id` called twice per message** | `app/handlers/messages.py:35` + `app/services/moderation.py:45` | Handler checks chat validity, then `ModerationService.process_message` checks it again. | Redundant DB query per message |

### MAJOR

| # | Defect | File | Lines | Impact |
|---|--------|------|-------|--------|
| M1 | **Alembic hardcodes DB URL** | `alembic.ini:3` + `migrations/env.py:41` | `sqlalchemy.url = postgresql+asyncpg://adcleaner:change_me@postgres:5432/adcleaner`. `env.py` never reads `DATABASE_URL` from the environment. | Migrations fail with non-default credentials |
| M2 | **Threading lock in async code** | `app/detector/service.py:21` | `threading.Lock()` for repeat-cache access. Blocks the event loop thread during cache operations. | Suboptimal, can block other tasks |
| M3 | **Broad `except Exception` in 7 locations** | Multiple (see section 18) | All Telegram API errors (rate limit, forbidden, timeout) are caught identically. No retry logic for rate limits. | Misses retriable vs non-retriable distinction |
| M4 | **Excerpt length hardcoded** | `app/services/moderation.py:114` | `(text or "")[:250]` — ignores `config.message_excerpt_max_length`. | Config value has no effect |
| M5 | **`delete_expired` loads all into memory** | `app/database/repositories/deletion_logs.py:75-77` | Single `DELETE` statement would be more efficient. | Scale concern |
| M6 | **`add_bot` dead code** | `app/services/allowlist.py:85-99` | Defined but never called from any handler. | Feature gap |
| M7 | **`notify_admins` dead code** | `app/services/notifications.py` | Defined but never called. | Feature gap |
| M8 | **Dead code in scoring pipeline** | `app/detector/scoring.py:134-136` | Empty `for` loop that does nothing. | Confusing |
| M9 | **`NEGATIVE_SIGNALS` never used** | `app/detector/scoring.py:34-36` | Defined but never referenced in scoring logic. | Feature gap |
| M10 | **`sample_texts` fixture never used** | `tests/conftest.py` | Defined globally, never imported by any test. | Waste |

### COSMETIC

| # | Defect | File | Lines | Impact |
|---|--------|------|-------|--------|
| D1 | Type annotation mismatch | `membership.py:18,57` | `_register_or_update_chat` annotated `-> None`, actually returns `bool` | Linter warning |
| D2 | `postgres_db/user/password` dead fields | `app/config.py:10-12` | Defined in Settings but never read by any code | Waste |
| D3 | 6 other dead functions | Multiple | `extract_entity_urls`, `extract_forward_info`, `utcnow` (utils), `hours_ago`, `minutes_ago`, `is_telegram_domain` | Waste |
| D4 | SQLite file not in `.gitignore` | `.gitignore` | `test_adcleaner.db` may be committed | Accidental commit |
| D5 | `FakeAllowlistRepo` duplicated in 2 test files | `tests/unit/test_scoring.py` + `tests/unit/test_detector_service.py` | Sync vs async variants | Maintenance burden |

---

## 4. Architectural Decisions

### AD-1: PostgreSQL Outbox over Message Queue
Use PostgreSQL as the job queue (`FOR UPDATE SKIP LOCKED`) rather than introducing Redis or Celery. Reason: zero additional infrastructure, transactional consistency with the database, sufficient for MVP scale.

### AD-2: One Bot Token, One Bot Instance
The AdCleaner bot remains the only Telegram-connected process. SecAdmin API never receives or stores the bot token. All Telegram actions go through the enforcement bridge.

### AD-3: FastAPI for SecAdmin API
Stick with Python async stack (FastAPI + async SQLAlchemy). Avoid introducing a second language.

### AD-4: React + TypeScript for Web UI
Chosen for ecosystem maturity, type safety with Zod validation, and TanStack Query's async state management.

### AD-5: AI Runs Monitor-Only by Default
No enforcement actions from AI without explicit configuration. AI may Recommend, but only humans may Execute.

### AD-6: Three-Tier Message Retention
- Safe messages: metadata only, 7 days
- AI observations: full text, 24 hours max
- Security events: evidence excerpt, 90 days
- Cases: per-case retention policy

### AD-7: pgvector for Embeddings
PostgreSQL extension for vector similarity search. Avoids a separate vector database.

### AD-8: Separate PostgreSQL Roles
- `adcleaner_bot` — RW for bot tables only
- `secadmin_api` — RW for secadmin tables only
- `secadmin_migrations` — DDL for all schemas
- `secadmin_reader` — RO for reporting

---

## 5. Proposed Final File Tree

```
reklama-tozalovchi-bot/
├── app/
│   ├── main.py                    # [MODIFY] Add observation producer setup
│   ├── config.py                  # [MODIFY] Add SecAdmin config fields
│   ├── logging_config.py          # [MODIFY] Add secadmin log file handler
│   │
│   ├── bot/
│   │   ├── filters.py             # UNCHANGED
│   │   ├── keyboards.py           # UNCHANGED
│   │   ├── middlewares.py         # UNCHANGED
│   │   └── commands.py            # UNCHANGED
│   │
│   ├── handlers/
│   │   ├── commands.py            # [MODIFY] Fix allowlist bugs (C6)
│   │   ├── messages.py            # [MODIFY] Pass mode, sender_id; add observation call
│   │   ├── edited_messages.py     # [MODIFY] Same fixes as messages.py
│   │   ├── membership.py          # [MODIFY] Fix double handler (C7); add user observation
│   │   └── private.py             # UNCHANGED
│   │
│   ├── services/
│   │   ├── moderation.py          # [MODIFY] Fix C1, C2, C3, C4, M4; add observation producer
│   │   ├── allowlist.py           # UNCHANGED
│   │   ├── permissions.py         # [MODIFY] Narrow exception handling
│   │   ├── cleanup.py             # [MODIFY] Add secadmin table cleanup
│   │   ├── notifications.py       # UNCHANGED (still dead)
│   │   ├── observation.py         # [NEW] Security observation producer
│   │   └── enforcement.py         # [NEW] Enforcement action consumer
│   │
│   ├── detector/
│   │   ├── service.py             # [MODIFY] Accept mode/sender_id, pass filtered URLs
│   │   ├── scoring.py             # [MODIFY] Accept sender_is_bot, add NEGATIVE_SIGNALS
│   │   ├── security.py            # [NEW] Fast security-threat detector
│   │   ├── phrases.py             # [MODIFY] Add security-related phrases
│   │   ├── normalizer.py          # UNCHANGED
│   │   ├── extractor.py           # [MODIFY] Add indicator extraction (IP, email, wallet)
│   │   └── models.py              # [MODIFY] Add SecurityResult
│   │
│   ├── database/
│   │   ├── base.py                # UNCHANGED
│   │   ├── session.py             # [MODIFY] Add secadmin engine
│   │   ├── models.py              # [MODIFY] Add secadmin models
│   │   └── repositories/
│   │       ├── chats.py           # UNCHANGED
│   │       ├── allowlist.py       # UNCHANGED
│   │       ├── deletion_logs.py   # [MODIFY] Fix expires_at (C5)
│   │       ├── observation.py     # [NEW] Security observation outbox repo
│   │       ├── events.py          # [NEW] Security events repo
│   │       ├── indicators.py      # [NEW] Threat indicators repo
│   │       ├── users.py           # [NEW] Observed users repo
│   │       ├── cases.py           # [NEW] Cases repo
│   │       ├── officers.py        # [NEW] Officers / auth repo
│   │       └── enforcement.py     # [NEW] Enforcement actions repo
│   │
│   ├── secadmin/
│   │   ├── __init__.py            # [NEW]
│   │   ├── worker.py              # [NEW] Background worker (observation consumer)
│   │   ├── ai/
│   │   │   ├── __init__.py        # [NEW]
│   │   │   ├── classifier.py      # [NEW] AI classifier interface
│   │   │   ├── provider_openai.py # [NEW] OpenAI-compatible provider
│   │   │   ├── provider_ollama.py # [NEW] Local Ollama provider
│   │   │   ├── provider_none.py   # [NEW] Disabled provider
│   │   │   └── embeddings.py      # [NEW] pgvector embedding service
│   │   └── rules/
│   │       ├── __init__.py        # [NEW]
│   │       ├── campaign.py        # [NEW] Cross-group campaign correlation
│   │       └── behaviour.py       # [NEW] User-risk behaviour scoring
│   │
│   └── utils/
│       ├── telegram.py            # DEAD — can be cleaned up later
│       └── time.py                # DEAD — can be cleaned up later
│
├── api/
│   ├── __init__.py                # [NEW]
│   ├── main.py                    # [NEW] FastAPI entry point
│   ├── config.py                  # [NEW] API-specific settings
│   ├── deps.py                    # [NEW] Dependency injection
│   ├── auth/
│   │   ├── __init__.py            # [NEW]
│   │   ├── router.py              # [NEW] Login/logout/session
│   │   ├── deps.py                # [NEW] Current-officer dependency
│   │   └── middleware.py          # [NEW] Session validation middleware
│   ├── routers/
│   │   ├── __init__.py            # [NEW]
│   │   ├── dashboard.py           # [NEW]
│   │   ├── events.py              # [NEW]
│   │   ├── indicators.py          # [NEW]
│   │   ├── users.py               # [NEW]
│   │   ├── groups.py              # [NEW]
│   │   ├── cases.py               # [NEW]
│   │   ├── officers.py            # [NEW]
│   │   ├── audit.py               # [NEW]
│   │   ├── enforcement.py         # [NEW]
│   │   ├── reports.py             # [NEW]
│   │   └── health.py              # [NEW]
│   └── schemas/
│       ├── __init__.py            # [NEW]
│       ├── auth.py                # [NEW] Pydantic request/response schemas
│       ├── events.py              # [NEW]
│       ├── indicators.py          # [NEW]
│       ├── users.py               # [NEW]
│       ├── groups.py              # [NEW]
│       ├── cases.py               # [NEW]
│       ├── officers.py            # [NEW]
│       ├── enforcement.py         # [NEW]
│       └── dashboard.py           # [NEW]
│
├── web/
│   ├── package.json               # [NEW]
│   ├── tsconfig.json              # [NEW]
│   ├── vite.config.ts             # [NEW]
│   ├── tailwind.config.ts         # [NEW]
│   ├── index.html                 # [NEW]
│   └── src/
│       ├── main.tsx               # [NEW]
│       ├── App.tsx                # [NEW]
│       ├── routes.tsx             # [NEW] React Router config
│       ├── api/
│       │   ├── client.ts          # [NEW] Axios/fetch client
│       │   └── queries.ts         # [NEW] TanStack Query hooks
│       ├── hooks/
│       │   ├── useAuth.ts         # [NEW]
│       │   └── useDebounce.ts     # [NEW]
│       ├── stores/
│       │   └── auth.ts            # [NEW] Auth context
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppShell.tsx   # [NEW] Sidebar + header layout
│       │   │   ├── Sidebar.tsx    # [NEW]
│       │   │   └── Header.tsx     # [NEW]
│       │   ├── ui/
│       │   │   ├── Badge.tsx      # [NEW]
│       │   │   ├── Button.tsx     # [NEW]
│       │   │   ├── Card.tsx       # [NEW]
│       │   │   ├── Modal.tsx      # [NEW]
│       │   │   ├── Table.tsx      # [NEW] TanStack Table wrapper
│       │   │   └── Spinner.tsx    # [NEW]
│       │   └── forms/
│       │       ├── LoginForm.tsx  # [NEW]
│       │       ├── CaseForm.tsx   # [NEW]
│       │       └── NoteForm.tsx   # [NEW]
│       └── pages/
│           ├── Login.tsx          # [NEW]
│           ├── Dashboard.tsx      # [NEW]
│           ├── Events.tsx         # [NEW]
│           ├── EventDetail.tsx    # [NEW]
│           ├── Indicators.tsx     # [NEW]
│           ├── Users.tsx          # [NEW]
│           ├── UserDetail.tsx     # [NEW]
│           ├── Groups.tsx         # [NEW]
│           ├── Cases.tsx          # [NEW]
│           ├── CaseDetail.tsx     # [NEW]
│           ├── Officers.tsx       # [NEW]
│           ├── AuditLog.tsx       # [NEW]
│           ├── Reports.tsx        # [NEW]
│           ├── Settings.tsx       # [NEW]
│           └── Health.tsx         # [NEW]
│
├── migrations/
│   ├── env.py                     # [MODIFY] Read DATABASE_URL from env
│   ├── versions/
│   │   ├── 0001_initial.py        # UNCHANGED
│   │   ├── 0002_fix_expires_at.py # [NEW] Fix C5
│   │   └── 0003_secadmin.py       # [NEW] All secadmin tables
│   └── script.py.mako             # UNCHANGED
│
├── tests/
│   ├── conftest.py                # [MODIFY] Shared fixtures
│   ├── unit/                      # [MODIFY] Add security detector tests
│   ├── integration/               # [MODIFY] Add secadmin repo tests
│   ├── services/                  # [NEW] Service-layer tests
│   ├── api/                       # [NEW] API endpoint tests
│   └── ai/                        # [NEW] AI worker tests
│
├── scripts/
│   ├── create_roles.sql           # [NEW] PostgreSQL role creation
│   └── seed_officer.py            # [NEW] First super-admin creation
│
├── docker-compose.yml             # [MODIFY] Add secadmin services
├── Dockerfile                     # [MODIFY] Multi-stage for API + worker
├── Dockerfile.api                 # [NEW] FastAPI container
├── Dockerfile.web                 # [NEW] React + Nginx container
├── Caddyfile                      # [NEW] Reverse proxy config
├── .env.example                   # [MODIFY] Add secadmin env vars
└── pyproject.toml                 # [MODIFY] Add secadmin dependencies
```

---

## 6. Service Boundaries

```
┌──────────────────────────────────────────────────────────────────┐
│                       Docker Network                             │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────────────────┐        │
│  │   adcleaner-bot   │    │      secadmin-worker         │        │
│  │   (Aiogram)       │    │   (Background Consumer)      │        │
│  │                   │    │                              │        │
│  │  Receives updates │    │  Reads observation outbox    │        │
│  │  Runs fast rules  │    │  Runs AI classification      │        │
│  │  Produces obs     │    │  Generates embeddings        │        │
│  │  Consumes enforce │    │  Correlates campaigns        │        │
│  │  Records results  │    │  Creates security events     │        │
│  └────────┬─────────┘    └──────────┬───────────────────┘        │
│           │                         │                            │
│           └──────────┬──────────────┘                            │
│                      │                                            │
│              ┌───────▼────────┐                                   │
│              │   PostgreSQL    │                                   │
│              │                 │                                   │
│              │  Bot tables     │                                   │
│              │  SecAdmin tables│                                   │
│              └───────┬────────┘                                   │
│                      │                                            │
│              ┌───────▼────────┐     ┌──────────────────────┐      │
│              │  secadmin-api   │────▶│    secadmin-web      │      │
│              │  (FastAPI)      │     │  (React + TS)       │      │
│              │                 │     │                      │      │
│              │  Auth + RBAC    │     │  Dashboard           │      │
│              │  REST endpoints │     │  Event Queue         │      │
│              └───────┬────────┘     │  Incident Detail     │      │
│                      │              │  Cases, Users, etc   │      │
│                      │              └──────────────────────┘      │
│              ┌───────▼────────┐                                   │
│              │  reverse-proxy  │                                   │
│              │  (Caddy)        │                                   │
│              │  HTTPS only     │                                   │
│              └────────────────┘                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User sends message
  → AdCleaner bot handler (messages.py)
    → ModerationService.process_message()
      → Existing ad detector
      → [NEW] Security detector (fast rules)
      → If obvious threat: delete immediately
      → [NEW] Insert observation record (outbox)
  → secadmin-worker claims observation (FOR UPDATE SKIP LOCKED)
    → Advanced security rules
    → AI classification
    → Embedding similarity check
    → Create security event (if suspicious)
    → Delete message content if safe
  → Officer reviews event in web UI
    → Officer takes action (confirm / false positive / delete message)
    → API creates enforcement action
  → AdCleaner bot claims enforcement action
    → Executes Telegram API call
    → Records outcome
```

---

## 7. Message-Processing Sequence (Modified)

### Phase 0: Current flow with bug fixes

```
handle_group_message(message, session)
  chat = await chat_repo.get_by_telegram_id(message.chat.id)
  if chat is None or not chat.enabled: return
  [MODIFY] Pass chat object → process_message to avoid duplicate query
  mod_service = ModerationService(session, bot)
  await mod_service.process_message(
      chat_id, message_id, text, sender_id, sender_is_bot,
      sender_chat_id, is_forwarded, forward_from_chat_id,
      entities, caption_entities,
      chat_mode=chat.mode,                    # [FIX C1]
  )
```

```
ModerationService.process_message(...)
  [FIX C8] Accept chat object, skip duplicate get_by_telegram_id
  [FIX C5] Pass proper expires_at to deletion log
  [FIX C4] Use filtered URLs in scoring
  analyze_kwargs = {
      "mode": chat_mode,                      # [FIX C1]
      "sender_id": sender_id,                # [FIX C2]
      "sender_is_bot": sender_is_bot,        # [FIX C3]
  }
  result = await self._detection.analyze(..., **analyze_kwargs)
  if result.is_advertisement:
      try to delete
      if succeed: create deletion log
      [MODIFY] Always create observation (even if delete fails)
```

### Phase 3+: With observation producer

```
ModerationService.process_message(...)
  ... (existing detection) ...

  [NEW] Build MessageContext
  context = MessageContext(
      chat_id=chat_id, message_id=message_id,
      text=text, sender_id=sender_id, sender_is_bot=sender_is_bot,
      entities=entities, is_forwarded=is_forwarded,
      forward_from_chat_id=forward_from_chat_id,
      ad_result=result,
      security_result=security_result,
      timestamp=now,
  )

  [NEW] Upsert observed user (background, non-blocking)
  [NEW] Insert observation into outbox
```

---

## 8. Database Model Plan

### MVP Tables (Phases 1-4)

#### `security_observation_outbox` — Outbox Job Queue
```
id              UUID PK
update_id       BIGINT UNIQUE             — Telegram update_id for dedup
chat_id         BIGINT NOT NULL           — Telegram chat ID
message_id      BIGINT NOT NULL           — Telegram message ID
sender_id       BIGINT                    — Telegram user ID
text_hash       VARCHAR(64)               — SHA-256 of normalized text
text            TEXT                      — Original text (temp, expires)
entities        JSONB                     — Telegram entities (temp, expires)
detection_result JSONB                    — Deterministic scores + reasons
urls            JSONB                     — Extracted URLs
telegram_entities JSONB                  — Extracted TG entities
status          VARCHAR(20) DEFAULT 'pending'
                  CHECK IN ('pending','claimed','completed','failed','expired')
retry_count     INT DEFAULT 0
max_retries     INT DEFAULT 3
locked_by       VARCHAR(64)               — Worker ID
locked_at       TIMESTAMPTZ
created_at      TIMESTAMPTZ
expires_at      TIMESTAMPTZ               — Text deleted after this
processed_at    TIMESTAMPTZ
```

Indexes: `(status, created_at)`, `(update_id)`, `(locked_by)`

#### `security_events` — Security Events
```
id                  UUID PK
event_number        BIGSERIAL UNIQUE      — Human-readable number
chat_id             BIGINT NOT NULL       — Telegram chat ID
message_id          BIGINT                — Telegram message ID
sender_id           BIGINT                — Telegram user ID
event_type          VARCHAR(50) NOT NULL  — See SecurityCategories
severity            VARCHAR(20) NOT NULL  — critical/high/medium/low/info
score               INT NOT NULL
confidence          FLOAT                 — 0.0 to 1.0 (AI confidence)
title               VARCHAR(255)          — Auto-generated summary
message_excerpt     TEXT                  — Short evidence excerpt (max 500 chars)
detection_reasons   JSONB                 — Array of reason strings
detected_indicators JSONB                 — Array of indicator IDs
ad_score            INT                   — From ad detector
security_score      INT                   — From security detector
ai_score            INT                   — From AI classifier
ai_analysis         JSONB                 — Full AI output
ai_model_id         UUID                  — FK to ai_model_registry
status              VARCHAR(20) DEFAULT 'open'
                      CHECK IN ('open','claimed','confirmed','false_positive','escalated','resolved')
assigned_officer_id BIGINT                — Telegram user ID of officer
case_id             UUID                  — FK to cases
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
expires_at          TIMESTAMPTZ           — 90-day default retention
```

Indexes: `(chat_id)`, `(sender_id)`, `(status, created_at)`, `(event_type)`, `(severity)`, `(expires_at)`

#### `indicators` — Threat Indicators
```
id                  UUID PK
indicator_type      VARCHAR(30) NOT NULL
                      CHECK IN ('domain','url','telegram_username','telegram_bot',
                                'telegram_chat','email','phone','wallet','ip',
                                'file_hash','message_hash')
indicator_value     TEXT NOT NULL         — Normalized value
status              VARCHAR(20) DEFAULT 'suspected'
                      CHECK IN ('suspected','confirmed','blocked','allowed','false_positive','expired')
first_seen_at       TIMESTAMPTZ
last_seen_at        TIMESTAMPTZ
seen_count          INT DEFAULT 1
event_count         INT DEFAULT 0
chat_ids            JSONB                 — Array of chat IDs where seen
notes               TEXT
created_by_officer_id BIGINT
created_at          TIMESTAMPTZ
```

Unique: `(indicator_type, indicator_value)`

#### `event_indicators` — Join Table
```
event_id            UUID FK → security_events
indicator_id        UUID FK → indicators
extracted_at        TIMESTAMPTZ
```

PK: `(event_id, indicator_id)`

#### `observed_users` — User Directory
```
telegram_id         BIGINT PK             — Telegram user ID
current_username    VARCHAR(255)
current_first_name  VARCHAR(255)
current_last_name   VARCHAR(255)
is_bot              BOOLEAN DEFAULT FALSE
language_code       VARCHAR(10)
is_premium          BOOLEAN DEFAULT FALSE
photo_id            VARCHAR(255)
first_seen_at       TIMESTAMPTZ
last_seen_at        TIMESTAMPTZ
risk_score          INT DEFAULT 0
risk_signals        JSONB
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

#### `user_chat_profiles` — Per-Group User Data
```
id                  UUID PK
user_id             BIGINT FK → observed_users(telegram_id)
chat_id             BIGINT NOT NULL       — Telegram chat ID
membership_status   VARCHAR(20)           — member/administrator/creator/restricted/left
is_admin            BOOLEAN DEFAULT FALSE
joined_at           TIMESTAMPTZ
left_at             TIMESTAMPTZ
message_count       INT DEFAULT 0
link_message_count  INT DEFAULT 0
deleted_message_count INT DEFAULT 0
security_event_count INT DEFAULT 0
confirmed_event_count INT DEFAULT 0
last_message_at     TIMESTAMPTZ
last_security_event_at TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

Unique: `(user_id, chat_id)`

#### `user_observed_names` — Name History
```
id                  UUID PK
user_id             BIGINT FK → observed_users(telegram_id)
username            VARCHAR(255)
first_name          VARCHAR(255)
last_name           VARCHAR(255)
first_seen_at       TIMESTAMPTZ
last_seen_at        TIMESTAMPTZ
```

Index: `(user_id)`

#### `member_risk_signals` — Behaviour Signals
```
id                  UUID PK
user_id             BIGINT FK → observed_users(telegram_id)
chat_id             BIGINT NOT NULL
signal_type         VARCHAR(50) NOT NULL  — See behaviour signals
signal_value        TEXT
detected_at         TIMESTAMPTZ
created_at          TIMESTAMPTZ
```

Index: `(user_id, chat_id)`

#### `officers` — Authorized Officers
```
id                  UUID PK
telegram_id         BIGINT UNIQUE NOT NULL
role                VARCHAR(20) NOT NULL DEFAULT 'analyst'
                      CHECK IN ('super_admin','analyst','responder','auditor')
display_name        VARCHAR(255)
is_active           BOOLEAN DEFAULT TRUE
last_login_at       TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

#### `officer_sessions` — API Sessions
```
id                  UUID PK
officer_id          UUID FK → officers
token_hash          VARCHAR(64) NOT NULL  — SHA-256 of session token
expires_at          TIMESTAMPTZ NOT NULL
created_at          TIMESTAMPTZ
revoked_at          TIMESTAMPTZ
ip_address          INET
user_agent          TEXT
```

#### `officer_audit_logs` — Immutable Audit Trail
```
id                  UUID PK
officer_id          UUID FK → officers
action_type         VARCHAR(50) NOT NULL
resource_type       VARCHAR(50)           — 'event','indicator','user','case',etc
resource_id         VARCHAR(255)          — UUID or external ID of resource
details             JSONB                 — Action-specific payload
created_at          TIMESTAMPTZ
```

Index: `(officer_id)`, `(resource_type, resource_id)`, `(created_at)`

#### `cases` — Investigation Cases
```
id                  UUID PK
case_number         BIGSERIAL UNIQUE
title               VARCHAR(500) NOT NULL
severity            VARCHAR(20) DEFAULT 'medium'
status              VARCHAR(20) DEFAULT 'open'
                      CHECK IN ('open','in_progress','resolved','closed')
assigned_officer_id BIGINT
description         TEXT
resolution          TEXT
resolved_at         TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

#### `case_events` — Events Linked to Case
```
id                  UUID PK
case_id             UUID FK → cases
event_id            UUID FK → security_events
added_by_officer_id BIGINT
added_at            TIMESTAMPTZ
```

Unique: `(case_id, event_id)`

#### `case_notes` — Investigation Notes
```
id                  UUID PK
case_id             UUID FK → cases
officer_id          BIGINT NOT NULL
content             TEXT NOT NULL
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

#### `enforcement_actions` — Telegram Action Queue
```
id                  UUID PK
action_type         VARCHAR(30) NOT NULL
                      CHECK IN ('delete_message','trust_sender','block_indicator',
                                'allow_indicator','refresh_member','refresh_group_permissions',
                                'restrict_member','mute_member','ban_member')
target_chat_id      BIGINT
target_message_id   BIGINT
target_user_id      BIGINT
target_indicator_id UUID
requested_by_officer_id BIGINT
status              VARCHAR(20) DEFAULT 'pending'
                      CHECK IN ('pending','claimed','completed','failed','cancelled')
result              JSONB                 — Telegram API response
locked_by           VARCHAR(64)
locked_at           TIMESTAMPTZ
created_at          TIMESTAMPTZ
completed_at        TIMESTAMPTZ
```

#### `telegram_query_requests` — User Detail Refresh
```
id                  UUID PK
query_type          VARCHAR(30) NOT NULL
                      CHECK IN ('get_chat_member','get_user_profile_photos',
                                'get_chat_administrators','get_chat_member_count','get_chat')
target_chat_id      BIGINT
target_user_id      BIGINT
requested_by_officer_id BIGINT
status              VARCHAR(20) DEFAULT 'pending'
result              JSONB
locked_by           VARCHAR(64)
created_at          TIMESTAMPTZ
completed_at        TIMESTAMPTZ
```

#### `ai_analysis_jobs` — AI Job Queue
```
id                  UUID PK
observation_id      UUID                  — FK → outbox
model_id            UUID
status              VARCHAR(20) DEFAULT 'pending'
input_text_hash     VARCHAR(64)
output              JSONB
error               TEXT
processing_time_ms  INT
created_at          TIMESTAMPTZ
processed_at        TIMESTAMPTZ
```

#### `ai_message_analyses` — AI Results
```
id                  UUID PK
job_id              UUID FK → ai_analysis_jobs
is_suspicious       BOOLEAN
category            VARCHAR(50)
risk_score          INT
confidence          FLOAT
reasons             JSONB
recommended_action  VARCHAR(20)
                     — 'allow','monitor','review','delete'
requires_human_review BOOLEAN
campaign_summary    TEXT
created_at          TIMESTAMPTZ
```

#### `message_embeddings` — pgvector Embeddings
```
id                  UUID PK
message_hash        VARCHAR(64) UNIQUE
text_hash           VARCHAR(64)
embedding           VECTOR(384)           — pgvector dimension (e.g., 384 for all-MiniLM-L6-v2)
model_id            UUID
created_at          TIMESTAMPTZ
```

#### `ai_feedback` — Officer Feedback on AI
```
id                  UUID PK
analysis_id         UUID FK → ai_message_analyses
officer_id          BIGINT
was_correct         BOOLEAN
correct_category    VARCHAR(50)
correct_score       INT
notes               TEXT
created_at          TIMESTAMPTZ
```

#### `ai_model_registry` — AI Model Tracking
```
id                  UUID PK
provider            VARCHAR(50)           — 'openai','ollama','disabled'
model_name          VARCHAR(255)
version             VARCHAR(50)
is_active           BOOLEAN DEFAULT TRUE
config              JSONB
created_at          TIMESTAMPTZ
```

#### `system_health_events` — Infrastructure Events
```
id                  UUID PK
event_type          VARCHAR(50)
                      — 'bot_disconnected','db_error','worker_crash',
                      — 'telegram_rate_limit','permission_changed','cleanup_status'
severity            VARCHAR(20)
message             TEXT
details             JSONB
created_at          TIMESTAMPTZ
expires_at          TIMESTAMPTZ
```

### Deferred Tables (Post-MVP)

- `attachment_scans` — ClamAV/YARA results
- `threat_feeds` — External threat intel
- `siem_exports` — SIEM integration queue
- `case_evidence_files` — Encrypted evidence storage
- `case_approvals` — Two-person approval records

---

## 9. Migration Plan

### Migration 0002: Fix Existing Issues
```python
# Fix expires_at in deletion_logs
# Retroactively set expires_at for NULL or expired records
op.execute("""
    UPDATE deletion_logs
    SET expires_at = created_at + INTERVAL '24 hours'
    WHERE expires_at <= created_at
""")
# Add UNIQUE constraint to allowed_entities if missing
op.create_unique_constraint(
    "uq_allowed_entity_per_chat",
    "allowed_entities",
    ["chat_id", "entity_type", "entity_value"],
)
```

### Migration 0003: SecAdmin Tables
Create all tables from section 8. Enable pgvector extension.

### Migration Strategy
- All migrations are forward-only (no downgrades for MVP)
- Each migration runs in its own transaction
- Migration order: 0001 (existing) → 0002 (fixes) → 0003 (secadmin)

---

## 10. API Endpoint Plan

### Authentication

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/login` | Create session (verify via Telegram login widget) | None |
| POST | `/api/v1/auth/logout` | Revoke session | Session |
| GET | `/api/v1/auth/me` | Current officer info | Session |

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/dashboard` | Aggregated stats (open alerts, critical events, pending reviews, active indicators, group health) |

### Events

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/events` | List events (paginated, filterable by status/severity/chat/type) |
| GET | `/api/v1/events/:id` | Event detail |
| PATCH | `/api/v1/events/:id` | Update event (claim, confirm, false positive, escalate, resolve) |
| PATCH | `/api/v1/events/bulk` | Bulk status update (non-destructive only) |
| GET | `/api/v1/events/:id/related` | Related events (same sender, same indicator) |

### Indicators

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/indicators` | List indicators (filterable by type/status) |
| GET | `/api/v1/indicators/:id` | Indicator detail with event list |
| PATCH | `/api/v1/indicators/:id` | Change indicator status |
| POST | `/api/v1/indicators` | Create indicator manually |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/users` | Search users by ID/username |
| GET | `/api/v1/users/:telegram_id` | User detail (profiles, events, risk signals) |
| POST | `/api/v1/users/:telegram_id/refresh` | Request Telegram detail refresh (creates query request) |

### Groups

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/groups` | List monitored groups |
| GET | `/api/v1/groups/:chat_id` | Group detail (bot status, mode, permissions, recent events) |
| PATCH | `/api/v1/groups/:chat_id` | Update group security policy (monitor-only, mode) |

### Cases

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/cases` | List cases |
| POST | `/api/v1/cases` | Create case |
| GET | `/api/v1/cases/:id` | Case detail (events, notes, timeline) |
| PATCH | `/api/v1/cases/:id` | Update case (assign, status, resolution) |
| POST | `/api/v1/cases/:id/notes` | Add note |
| POST | `/api/v1/cases/:id/events` | Link event to case |
| DELETE | `/api/v1/cases/:id/events/:event_id` | Remove event from case |

### Enforcement

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/enforcement/delete-message` | Request message deletion |
| POST | `/api/v1/enforcement/trust-sender` | Trust sender (add to allowlist) |
| POST | `/api/v1/enforcement/block-indicator` | Block indicator |
| POST | `/api/v1/enforcement/allow-indicator` | Allow indicator |
| POST | `/api/v1/enforcement/refresh-member` | Request user detail refresh |
| POST | `/api/v1/enforcement/refresh-group` | Request group permission refresh |
| GET | `/api/v1/enforcement` | List enforcement actions |

### Officers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/officers` | List officers |
| POST | `/api/v1/officers` | Create officer (super_admin only) |
| PATCH | `/api/v1/officers/:id` | Update officer role/status |
| DELETE | `/api/v1/officers/:id` | Deactivate officer |

### Audit

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/audit` | List audit log entries (filterable, paginated) |
| GET | `/api/v1/audit/export` | CSV export |

### Reports

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports/events.csv` | Security events CSV |
| GET | `/api/v1/reports/indicators.csv` | Indicators CSV |
| GET | `/api/v1/reports/cases/:id.json` | Case JSON export |
| GET | `/api/v1/reports/audit.csv` | Audit log CSV |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | System health (bot connectivity, DB, worker, API) |

---

## 11. Frontend Page and Component Plan

### Page Tree

```
/login                          → Login.tsx
/dashboard                      → Dashboard.tsx (requires auth)
/events                          → Events.tsx
/events/:id                      → EventDetail.tsx
/indicators                      → Indicators.tsx
/users                           → Users.tsx
/users/:telegram_id              → UserDetail.tsx
/groups                          → Groups.tsx
/cases                           → Cases.tsx
/cases/:id                       → CaseDetail.tsx
/officers                        → Officers.tsx
/audit                           → AuditLog.tsx
/reports                         → Reports.tsx
/settings                        → Settings.tsx
/health                          → Health.tsx
```

### Component Hierarchy

```
App
├── AuthProvider
│   ├── LoginPage
│   └── AuthenticatedLayout
│       ├── AppShell
│       │   ├── Sidebar (nav links, user info, logout)
│       │   ├── Header (breadcrumbs, search, notifications)
│       │   └── MainContent
│       │       ├── DashboardPage
│       │       │   ├── StatCard (×6: open alerts, critical, pending, groups, indicators, health)
│       │       │   ├── ThreatTrendChart (Recharts line chart)
│       │       │   ├── TopIndicators (mini table)
│       │       │   └── RecentActivity (timeline)
│       │       ├── EventsPage
│       │       │   ├── FilterBar (status, severity, chat, type, date range)
│       │       │   └── EventsTable (TanStack Table)
│       │       │       └── Row: time, group, sender, severity, type, indicator, status, actions
│       │       ├── EventDetailPage
│       │       │   ├── EventHeader (number, score, severity, status badge)
│       │       │   ├── MessageExcerpt
│       │       │   ├── DetectionReasons
│       │       │   ├── AIAnalysisCard
│       │       │   ├── IndicatorsSection
│       │       │   │   └── IndicatorRow (type, value, status, block/allow button)
│       │       │   ├── SenderInfoCard
│       │       │   ├── GroupInfoCard
│       │       │   ├── EnforcementResultCard
│       │       │   ├── RelatedEventsCard
│       │       │   ├── ReviewHistoryCard
│       │       │   └── ActionButtons (claim, confirm, false positive, escalate, resolve,
│       │       │                     delete message, block indicator, trust sender, open case)
│       │       ├── IndicatorsPage
│       │       │   ├── FilterBar (type, status)
│       │       │   └── IndicatorsTable
│       │       ├── UsersPage
│       │       │   ├── SearchBar
│       │       │   └── UsersTable
│       │       ├── UserDetailPage
│       │       │   ├── UserHeader (ID, username, name, photo, risk badge)
│       │       │   ├── GroupMembershipCard (table of groups)
│       │       │   ├── MessageStatsCard
│       │       │   ├── RiskSignalsCard
│       │       │   ├── SecurityEventsCard
│       │       │   └── RefreshButton
│       │       ├── GroupsPage
│       │       │   └── GroupsTable (bot status, mode, permissions, monitoring, actions)
│       │       ├── CasesPage
│       │       │   ├── CreateCaseButton
│       │       │   └── CasesTable (number, title, severity, status, assigned, updated)
│       │       ├── CaseDetailPage
│       │       │   ├── CaseHeader (number, title, severity badge, status)
│       │       │   ├── DescriptionEditable
│       │       │   ├── EventsSection (linked events table)
│       │       │   ├── NotesSection
│       │       │   │   ├── NoteList
│       │       │   │   └── NoteForm
│       │       │   ├── TimelineCard
│       │       │   ├── ResolutionForm
│       │       │   └── ExportButton
│       │       ├── OfficersPage
│       │       │   ├── CreateOfficerForm (super_admin only)
│       │       │   └── OfficersTable (name, telegram ID, role, active, last login)
│       │       ├── AuditLogPage
│       │       │   ├── FilterBar (action type, officer, date range)
│       │       │   └── AuditTable
│       │       ├── ReportsPage
│       │       │   ├── EventCSVButton
│       │       │   ├── IndicatorCSVButton
│       │       │   ├── AuditCSVButton
│       │       │   └── CaseExportButton (with case selector)
│       │       ├── SettingsPage
│       │       │   ├── GlobalModeToggle (monitor-only, ai monitor-only)
│       │       │   ├── RetentionSettings
│       │       │   ├── AISettings
│       │       │   └── KillSwitch
│       │       └── HealthPage
│       │           ├── BotConnectivityCard (green/red indicator)
│       │           ├── DatabaseHealthCard
│       │           ├── WorkerHealthCard
│       │           ├── APILatencyCard
│       │           └── RecentHealthEventsTable
```

### State Management

- Auth state: React Context (token, officer info, role)
- Server state: TanStack Query (caching, pagination, optimistic updates)
- Form state: React Hook Form + Zod validation
- URL state: React Router params/search params (filters, pagination)

---

## 12. AI Integration Plan

### Architecture

```
┌──────────────────────────────────────────────────┐
│                  AI Provider Interface             │
│  classify(text, indicators, scores) → AIResult    │
│  embed(text) → list[float]                        │
├──────────────────────────────────────────────────┤
│  Providers:                                       │
│  - OpenAIProvider (hosted API)                    │
│  - OllamaProvider (local)                         │
│  - DisabledProvider (no-op)                       │
└──────────────────────────────────────────────────┘
```

### Provider Interface (`app/secadmin/ai/classifier.py`)

```python
class AIProvider(ABC):
    @abstractmethod
    async def classify(
        self,
        text: str,
        indicators: list[str],
        scores: dict[str, int],
        language: str | None = None,
    ) -> AIClassificationResult: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...
```

### Classification Prompt

System prompt template:
```
You are a security analyst for a Telegram group moderation platform.
Analyze the following message for security threats.

Context:
- Deterministic ad score: {ad_score}/{threshold}
- Detected categories: {categories}
- Extracted indicators: {indicators}
- Group language: {language}

Message text:
```
{message_text}
```

Respond with valid JSON only:
{
  "is_suspicious": true/false,
  "category": "phishing/credential_theft/...",
  "risk_score": 0-10,
  "confidence": 0.0-1.0,
  "reasons": ["reason1", "reason2"],
  "recommended_action": "allow/monitor/review/delete",
  "requires_human_review": true/false,
  "campaign_summary": "Brief description or null"
}
```

### Safety Measures

- Structured output parsing with Pydantic validation
- Input length limit: 4000 characters (truncate before sending)
- Redact: OTP codes (regex `\b\d{4,8}\b`), seed phrases, private keys
- No tool-calling permissions
- No SQL generation from model output
- No direct Telegram access from model
- All outputs validated against schema before any action
- Timeout: 30 seconds per classification
- Retry: 1 retry on non-JSON response, then fall through to "requires_human_review"

### Monitor-Only Mode

- AI classification runs for ALL observations
- Output stored in `ai_message_analyses` table
- Security events are created based on AI + deterministic scores
- No automated enforcement actions from AI (even "delete" recommendation)
- AI "delete" recommendation is treated as "review"
- Monitor-only enforced at database level (column `ai_monitor_only` in group settings)

### Embedding Flow

```
Message arrives
  → Generate embedding (AI provider)
  → Query pgvector: similar messages within 7 days
  → If similarity > 0.85: flag as repeat campaign
  → Store embedding in message_embeddings
  → Cleanup: delete embeddings > 90 days
```

### MVP AI Provider

Start with the disabled provider. Add OpenAI-compatible API support in a config toggle. Local Ollama is deferred.

---

## 13. Member Observation Plan

### Observed Events

| Event | AdCleaner Handler | Action |
|-------|-------------------|--------|
| User sends message | `messages.py` | Upsert observed user, increment message count |
| User joins | `chat_member` update (new) | Upsert user, set membership_status='member', record joined_at |
| User leaves | `chat_member` update (new) | Update membership_status='left', record left_at |
| User promoted | `chat_member` update (new) | Set is_admin=True, record promotion |
| User demoted | `chat_member` update (new) | Set is_admin=False, record demotion |
| User restricted | `chat_member` update (new) | Update membership_status='restricted' |
| User changes name | `messages.py` | Record in user_observed_names |
| Bot command used | `commands.py` | Increment command count |
| Message deleted | `moderation.py` | Increment deleted_message_count |
| Security event created | `secadmin-worker` | Increment security_event_count |
| User confirmed false positive | API | Add false_positive signal |

### Chat Member Update Handler (New)

Current handlers only track `my_chat_member` (bot's own membership). Need to add `chat_member` updates for other users:

```python
@router.chat_member()
async def on_chat_member_update(event: types.ChatMemberUpdated, session=None) -> None:
    """Track user membership changes."""
    user_id = event.new_chat_member.user.id
    chat_id = event.chat.id
    new_status = event.new_chat_member.status
    # Upsert observed user
    # Upsert/update user_chat_profiles
    # Add signal if new_status == 'member' (just joined)
```

### User Detail Refresh Flow

```
Officer clicks "Refresh" in web UI
  → POST /api/v1/users/:id/refresh
    → API validates RBAC, creates telegram_query_requests record
  → AdCleaner bot polls telegram_query_requests WHERE status='pending'
    → Executes appropriate Telegram API call
    → Stores result in telegram_query_requests.result
    → Updates observed_users or user_chat_profiles
  → API polls for completion, returns result
```

**Telegram API limitation**: `get_chat_member` requires `chat_id`. If a user is not in any group where the bot is present, the bot cannot query them. The refresh button is only available for users with an observed group membership.

---

## 14. Telegram Query Bridge Plan

### Flow

```
1. API creates record in telegram_query_requests
2. AdCleaner bot has a periodic task: poll telegram_query_requests
   WHERE status='pending' ORDER BY created_at LIMIT 5 FOR UPDATE SKIP LOCKED
3. Bot executes the Telegram call
4. Bot writes result back to telegram_query_requests.result
5. Bot sets status = 'completed' (or 'failed')
6. (Optional) Bot updates local cache (observed_users, user_chat_profiles)
```

### Polling Implementation

```python
async def process_query_requests(bot: Bot, session: AsyncSession) -> None:
    repo = TelegramQueryRepository(session)
    requests = await repo.claim_pending(limit=5, worker_id=WORKER_ID)
    for req in requests:
        try:
            if req.query_type == "get_chat_member":
                result = await bot.get_chat_member(req.target_chat_id, req.target_user_id)
            elif req.query_type == "get_user_profile_photos":
                result = await bot.get_user_profile_photos(req.target_user_id)
            elif req.query_type == "get_chat_administrators":
                result = await bot.get_chat_administrators(req.target_chat_id)
            elif req.query_type == "get_chat_member_count":
                result = await bot.get_chat_member_count(req.target_chat_id)
            elif req.query_type == "get_chat":
                result = await bot.get_chat(req.target_chat_id)
            # Serialize result to JSON-safe dict
            await repo.complete(req.id, result=serialize(result))
        except Exception as e:
            await repo.fail(req.id, error=str(e))
```

### Security

- Bot never exposes its token to the API
- Query requests are scoped: an officer can only request refresh for users in groups they have access to
- Rate limiting: max 1 refresh per user per 60 seconds
- API validates chat_id exists in monitored groups before creating request

---

## 15. Enforcement Bridge Plan

### Flow

```
1. Officer clicks "Delete message" in web UI
2. POST /api/v1/enforcement/delete-message
3. API validates:
   - Officer has 'responder' role (or above)
   - Group is monitored by this bot
   - Event exists and is not already resolved
4. API creates enforcement_actions record (status='pending')
5. AdCleaner bot polls enforcement_actions WHERE status='pending'
   FOR UPDATE SKIP LOCKED
6. Bot executes Telegram API call
7. Bot records result in enforcement_actions.result
8. Bot sets status = 'completed' or 'failed'
9. Audit log created
```

### Action Implementations

| Action | Telegram Call | Success Criteria |
|--------|---------------|-----------------|
| `delete_message` | `bot.delete_message(chat_id, message_id)` | No exception |
| `trust_sender` | Add to allowlist (`AllowlistService`) | DB insert succeeds |
| `block_indicator` | Update indicator status to 'blocked' | DB update succeeds |
| `allow_indicator` | Update indicator status to 'allowed' | DB update succeeds |
| `refresh_member` | Create `telegram_query_requests` record | Insert succeeds |
| `refresh_group_permissions` | `bot_can_delete_messages()` + update DB | API call succeeds |

### Rate Limiting

- Max 10 enforcement actions per minute per chat (configurable)
- Duplicate detection: same `(action_type, target_chat_id, target_message_id)` within 60 seconds returns existing pending action
- Global kill switch: `enforcement_kill_switch` in `group_security_policies` — when enabled, all enforcement requests are immediately set to 'cancelled' with reason "kill switch active"

---

## 16. Security and Privacy Plan

### Data Retention

| Data Type | Retention | Enforcement |
|-----------|-----------|-------------|
| Safe message metadata | 7 days | `WHERE created_at < NOW() - INTERVAL '7 days'` — cleanup task deletes |
| AI observation text | 24 hours | `WHERE status IN ('completed','failed') AND expires_at < NOW()` — cleanup task deletes text field, keeps metadata |
| Security events | 90 days | `WHERE expires_at < NOW()` — cleanup task deletes entire row |
| Cases | Per-case policy | Cases marked 'closed' and older than retention setting are flagged for review |
| Embargoed evidence | Per-case policy | Encrypted storage with separate rotation |
| Audit logs | 1 year | Bulk export and archive before delete |

### Access Control

- All API endpoints check RBAC before any mutation
- Event detail: officer can only see events from groups they monitor
- User search: restricted to users observed in groups the officer can access
- Case access: only assigned officer + super_admin
- Audit log: readable by all officers, no deletion

### Secret Management

- Bot token: environment variable only, never stored in database, never exposed in API responses
- Database credentials: environment variables, separate roles per service
- Session tokens: HTTP-only cookies, SHA-256 hashed in database
- AI API keys: environment variables, never logged

### Audit Trail

Every officer action that modifies state creates an audit log entry:

| Action Type | Fields Recorded |
|-------------|-----------------|
| `event_status_change` | event_id, old_status, new_status |
| `indicator_status_change` | indicator_id, old_status, new_status |
| `enforcement_request` | action_id, action_type, target |
| `case_created` | case_id, officer_id |
| `case_assigned` | case_id, old_officer, new_officer |
| `officer_created` | new_officer_id, role |
| `officer_role_changed` | officer_id, old_role, new_role |
| `login` | session_id, officer_id |
| `settings_change` | setting_name, old_value, new_value |

### Security Requirements Checklist

- [ ] Separate PostgreSQL roles per service
- [ ] HTTP-only cookies with Secure flag
- [ ] CSRF protection via SameSite=Strict + token header
- [ ] Origin validation on all API requests
- [ ] Strict CORS (only the web origin)
- [ ] Rate limiting per officer (100 req/min)
- [ ] Rate limiting per endpoint (enforcement: 10/min)
- [ ] Idempotency keys on enforcement endpoints
- [ ] Input validation (Pydantic + Zod)
- [ ] No SQL injection (parameterized queries throughout)
- [ ] Session expiration (24h) + revocation
- [ ] Re-authentication for destructive actions
- [ ] No plaintext secrets in logs
- [ ] No AI output executed as code
- [ ] Container runs as non-root
- [ ] Internal network isolation

---

## 17. Docker and Deployment Plan

### Docker Compose Services

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_MULTIPLE_EXTENSIONS: pgcrypto,pgvector
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/create_roles.sql:/docker-entrypoint-initdb.d/01_create_roles.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
    restart: unless-stopped
    networks:
      - internal

  adcleaner-bot:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      BOT_TOKEN: ${BOT_TOKEN}
      DATABASE_URL: postgresql+asyncpg://adcleaner_bot:${BOT_DB_PASSWORD}@postgres:5432/adcleaner
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      DEFAULT_MODE: ${DEFAULT_MODE:-normal}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - internal

  secadmin-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: worker
    command: python -m app.secadmin.worker
    environment:
      DATABASE_URL: postgresql+asyncpg://secadmin_api:${API_DB_PASSWORD}@postgres:5432/adcleaner
      AI_PROVIDER: ${AI_PROVIDER:-disabled}
      AI_API_KEY: ${AI_API_KEY:-}
      AI_MODEL: ${AI_MODEL:-}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - internal

  secadmin-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql+asyncpg://secadmin_api:${API_DB_PASSWORD}@postgres:5432/adcleaner
      SESSION_SECRET: ${SESSION_SECRET}
      CORS_ORIGIN: https://secadmin.example.com
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - internal
      - public

  secadmin-web:
    build:
      context: ./web
      dockerfile: Dockerfile.web
    depends_on:
      - secadmin-api
    restart: unless-stopped
    networks:
      - public

  reverse-proxy:
    image: caddy:2-alpine
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - secadmin-api
      - secadmin-web
    restart: unless-stopped
    networks:
      - public

networks:
  internal:
    internal: true  # No external access
  public:

volumes:
  pgdata:
  caddy_data:
```

### Environment Variables (Additions to `.env.example`)

```
# Database roles
BOT_DB_PASSWORD=change_me_bot
API_DB_PASSWORD=change_me_api
MIGRATIONS_DB_PASSWORD=change_me_migrations
READER_DB_PASSWORD=change_me_reader

# SecAdmin API
SESSION_SECRET=generate_a_strong_random_secret_here
CORS_ORIGIN=https://secadmin.example.com

# AI (optional)
AI_PROVIDER=disabled
AI_API_KEY=
AI_MODEL=

# Retention
EVENT_RETENTION_DAYS=90
OBSERVATION_TEXT_HOURS=24
METADATA_RETENTION_DAYS=7
```

### Health Checks

| Service | Check | Interval |
|---------|-------|----------|
| postgres | `pg_isready` | 5s |
| adcleaner-bot | (None — uses restart) | — |
| secadmin-worker | HTTP GET `/health` | 30s |
| secadmin-api | HTTP GET `/api/v1/health` | 15s |
| secadmin-web | Serves static files via nginx | — |
| reverse-proxy | (Caddy built-in) | — |

### Migration Strategy

- Migrations run via Alembic at container startup
- `adcleaner-bot` entrypoint runs `alembic upgrade head`
- `secadmin-api` entrypoint also runs `alembic upgrade head` (safe with concurrent runs due to Alembic's lock table)
- In production, run migrations as a one-shot job, not at startup

---

## 18. Test Plan

### Phase 0 Tests (Existing AdCleaner Repairs)

| Test | File | What It Verifies |
|------|------|------------------|
| `test_mode_passed_to_detector` | NEW: `tests/unit/test_moderation.py` | C1: chat.mode reaches DetectionService.analyze() |
| `test_sender_id_passed_to_detector` | NEW | C2: sender_id forwarded |
| `test_sender_is_bot_passed` | NEW | C3: sender_is_bot forwarded |
| `test_whitelisted_domain_excluded_from_score` | NEW | C4: filtered URLs used in scoring_pipeline |
| `test_deletion_log_expires_properly` | `tests/integration/test_deletion_logs_repository.py` | C5: expires_at = created_at + retention |
| `test_allowlist_by_username_matches` | NEW: `tests/unit/test_moderation.py` | C6: username-based allowlist entries match sender_id |
| `test_membership_handler_no_duplicate` | NEW: `tests/integration/test_membership.py` | C7: promotion event doesn't trigger double registration |
| `test_single_get_by_telegram_id` | NEW | C8: process_message accepts chat object |

### Security Detector Tests

| Test | What It Verifies |
|------|------------------|
| `test_phishing_detected` | Message containing "verify your account" + fake login link |
| `test_otp_theft_detected` | "Send me the code that was sent to your number" |
| `test_seed_phrase_detected` | "Enter your 12-word recovery phrase" |
| `test_private_key_detected` | "Your private key" in message text |
| `test_fake_support_detected` | "Telegram support" + @username impersonation |
| `test_investment_fraud_detected` | "Guaranteed 1000% returns" + Telegram group invite |
| `test_crypto_scam_detected` | "Send ETH to this address" |
| `test_malware_link_detected` | URL with `.exe` download + "install this app" |
| `test_suspicious_bot_detected` | Unknown bot posting promotions |
| `test_impersonation_detected` | Display name = admin name + promotion content |
| `test_repeated_campaign_detected` | Same message hash within 24h across groups |
| `test_edited_message_escalation` | Message edited from safe to include URL |
| `test_secret_exposure_detected` | Message containing "API_KEY" or "token" |

### Observation Outbox Tests

| Test | What It Verifies |
|------|------------------|
| `test_observation_created` | ModerationService creates outbox record after processing |
| `test_update_id_dedup` | Same update_id doesn't create duplicate |
| `test_job_claiming` | FOR UPDATE SKIP LOCKED works |
| `test_job_retry` | Failed job increments retry_count |
| `test_job_expiration` | Old pending jobs are expired |
| `test_concurrent_workers` | Two workers don't claim same job |

### AI Worker Tests

| Test | What It Verifies |
|------|------------------|
| `test_structured_output_parsing` | Valid JSON output from AI is parsed correctly |
| `test_invalid_json_handling` | Non-JSON output triggers retry |
| `test_provider_timeout` | 30s timeout triggers fallback |
| `test_prompt_injection_resistance` | "Ignore previous instructions" in message |
| `test_embedding_similarity` | Similar messages return high cosine similarity |
| `test_monitor_only_enforced` | AI "delete" recommendation doesn't create enforcement |
| `test_disabled_provider_returns_null` | DisabledProvider returns None |

### API Tests

| Test | What It Verifies |
|------|------------------|
| `test_login_with_valid_telegram_id` | Session created |
| `test_login_without_officer_record` | 401 |
| `test_session_expiry` | Expired session returns 401 |
| `test_analyst_cannot_delete_messages` | RBAC enforced |
| `test_responder_can_delete_messages` | RBAC enforced |
| `test_auditor_read_only` | Auditor cannot mutate |
| `test_event_workflow` | open → claimed → confirmed |
| `test_bulk_status_update` | Multiple events updated atomically |
| `test_indicator_block_then_unblock` | Status transitions validated |
| `test_enforcement_request_creates_action` | POST creates pending action |
| `test_cross_group_access_denied` | Officer cannot see unauthorized groups |
| `test_audit_log_created_on_action` | Every mutation creates audit entry |

### Frontend Tests

| Test | What It Verifies |
|------|------------------|
| `unauthenticated_redirect_to_login` | Protected routes redirect |
| `login_form_submission` | API call + redirect |
| `event_filters_persist_in_url` | Filter params in URL search |
| `incident_detail_loads_correctly` | Event data rendered |
| `role_based_buttons_hidden` | Non-responder can't see delete button |
| `error_state_shown_on_api_failure` | Error boundary renders |
| `modal_interaction_flow` | Confirm/cancel workflows |
| `pagination_works` | Next/prev page loads data |

### Integration Tests

| Test | What It Verifies |
|------|------------------|
| `ad_observation_to_security_event` | Full flow: message → outbox → worker → event |
| `enforcement_request_to_telegram_action` | Full flow: API → enforcement → bot → result |
| `retention_cleanup_deletes_expired` | Cleanup task removes old data |
| `docker_services_start` | Docker Compose up succeeds |
| `alembic_migration_runs` | `alembic upgrade head` succeeds |

---

## 19. Phased Implementation Roadmap

### Phase 0 — Repository Repairs (Estimated: 3-5 days)

**Goal**: Fix all CRITICAL and MAJOR defects before adding new features.

**Files to modify**:
- `app/services/moderation.py` — Fix C1, C2, C3, C4, M4
- `app/detector/service.py` — Fix C4 (use filtered URLs)
- `app/handlers/messages.py` — Pass chat object to process_message (C8)
- `app/handlers/membership.py` — Fix C7 (remove catch-all, update _register_or_update_chat)
- `app/database/repositories/deletion_logs.py` — Fix C5
- `app/services/permissions.py` — M3 (narrow exceptions)
- `migrations/env.py` — Fix M1 (read DATABASE_URL from env)
- `alembic.ini` — Remove hardcoded URL
- `.gitignore` — Add `test_adcleaner.db`

**Files to create**:
- `migrations/versions/0002_fix_expires_at.py`

**Exit criteria**:
- [ ] All 8 critical bugs fixed and verified by tests
- [ ] All 69 existing tests still pass
- [ ] 8+ new tests for fixed bugs
- [ ] Alembic migrations work with environment-provided DATABASE_URL
- [ ] `ruff check` passes
- [ ] Manual verification: mode changes affect detection, allowlist @username works, deletion logs persist

---

### Phase 1 — Shared Data Foundation (Estimated: 3-4 days)

**Goal**: Add all secadmin database models, repositories, outbox infrastructure.

**Files to create**:
- `app/database/repositories/observation.py`
- `app/database/repositories/events.py`
- `app/database/repositories/indicators.py`
- `app/database/repositories/users.py`
- `app/database/repositories/cases.py`
- `app/database/repositories/officers.py`
- `app/database/repositories/enforcement.py`
- `migrations/versions/0003_secadmin.py`

**Files to modify**:
- `app/database/models.py` — Add all secadmin models
- `app/database/__init__.py` — Export new models
- `pyproject.toml` — Add psycopg2-binary (for migrations), pgvector

**Exit criteria**:
- [ ] All 27 new models defined with proper types, constraints, indexes
- [ ] All repositories implemented with CRUD + specific queries
- [ ] Outbox supports `FOR UPDATE SKIP LOCKED`
- [ ] Migration creates tables without errors
- [ ] Integration tests for all new repositories

---

### Phase 2 — Member Observation (Estimated: 3-4 days)

**Goal**: Build observed-user directory, membership tracking, Telegram query bridge.

**Files to create**:
- `app/database/repositories/telegram_queries.py` (if not in Phase 1)
- `app/bot/member_observer.py` — Chat member update handler

**Files to modify**:
- `app/handlers/messages.py` — Add user upsert on message
- `app/handlers/membership.py` — Add user upsert on bot events
- `app/main.py` — Register chat_member router, start query processor task
- `app/services/permissions.py` — Add user refresh flow

**Exit criteria**:
- [ ] Observed users created from messages, joins, leaves
- [ ] Name changes tracked
- [ ] Per-group membership profiles maintained
- [ ] Telegram query bridge works (refresh button → API → bot → Telegram → result)

---

### Phase 3 — Security Observation Producer (Estimated: 4-5 days)

**Goal**: Add MessageContext, fast security rules, observation outbox production.

**Files to create**:
- `app/detector/security.py` — Fast security threat detector
- `app/detector/models.py` — Add SecurityResult
- `app/detector/extractor.py` — Add IP, email, wallet, phone extraction
- `app/services/observation.py` — Observation producer service

**Files to modify**:
- `app/services/moderation.py` — Add observation production, security detection call
- `app/handlers/messages.py` — Pass full context
- `app/handlers/edited_messages.py` — Same
- `app/detector/phrases.py` — Add security-related phrases

**Exit criteria**:
- [ ] Security detector identifies phishing, credentials, fraud, malware signals
- [ ] Indicator extraction covers all required types
- [ ] Every processed message creates an observation (or skips if safe)
- [ ] Outbox deduplication works (by update_id)
- [ ] Message text deleted after 24h from outbox records

---

### Phase 4 — SecAdmin Worker (Estimated: 4-5 days)

**Goal**: Background worker consumes observations, creates events, correlates indicators.

**Files to create**:
- `app/secadmin/__init__.py`
- `app/secadmin/worker.py` — Main worker loop
- `app/secadmin/rules/campaign.py`
- `app/secadmin/rules/behaviour.py`

**Files to modify**:
- `app/main.py` — (No changes — worker is separate process)
- `pyproject.toml` — Add httpx (for AI API calls)

**Exit criteria**:
- [ ] Worker claims and processes observations
- [ ] Security events created for suspicious content
- [ ] Indicators extracted and stored
- [ ] User risk scores updated
- [ ] Campaign correlation across groups
- [ ] Expired observation text deleted
- [ ] Worker handles restart gracefully

---

### Phase 5 — SecAdmin API (Estimated: 5-7 days)

**Goal**: FastAPI backend with auth, RBAC, all endpoints.

**Files to create**:
- All `api/` tree as defined in section 5
- `Dockerfile.api`
- `scripts/create_roles.sql`
- `scripts/seed_officer.py`

**Files to modify**:
- `pyproject.toml` — Add FastAPI deps
- `docker-compose.yml` — Add secadmin-api service

**Exit criteria**:
- [ ] Authentication via Telegram login widget or pre-shared key
- [ ] Session management (create, validate, expire, revoke)
- [ ] RBAC enforced on all endpoints
- [ ] All 40+ endpoints implemented and tested
- [ ] Audit logging on all mutations
- [ ] Pagination, filtering, sorting on list endpoints
- [ ] Rate limiting active
- [ ] CORS configured
- [ ] Health endpoint returns accurate status

---

### Phase 6 — SecAdmin Web UI (Estimated: 7-10 days)

**Goal**: React + TypeScript frontend with all pages.

**Files to create**:
- All `web/` tree as defined in section 5
- `Dockerfile.web`

**Files to modify**:
- `docker-compose.yml` — Add secadmin-web service
- `Caddyfile` — Route `/api/*` to API, `/*` to web

**Exit criteria**:
- [ ] Login page works
- [ ] Dashboard loads with real data
- [ ] Event queue with filters, sorting, pagination
- [ ] Event detail with all actions
- [ ] Indicator management
- [ ] User search and detail
- [ ] Groups overview
- [ ] Cases CRUD with notes and timeline
- [ ] Officer management
- [ ] Audit log view
- [ ] Reports download
- [ ] Settings page (monitor-only toggles)
- [ ] System health page
- [ ] Role-based UI (buttons hidden for unauthorized roles)
- [ ] Responsive layout works

---

### Phase 7 — Enforcement Bridge (Estimated: 3-4 days)

**Goal**: AdCleaner consumes enforcement actions, executes Telegram calls.

**Files to create**:
- `app/services/enforcement.py`

**Files to modify**:
- `app/main.py` — Start enforcement consumer task
- `app/services/allowlist.py` — Add trust-sender programmatic path
- `app/services/permissions.py` — Add refresh-group-permissions action

**Exit criteria**:
- [ ] Delete message action works end-to-end
- [ ] Trust sender action adds to allowlist and creates deletion log
- [ ] Block/allow indicator updates DB
- [ ] Refresh member creates query request
- [ ] Refresh group permissions re-checks bot status
- [ ] Enforcement kill switch respected
- [ ] Rate limiting enforced per chat

---

### Phase 8 — AI Monitor-Only (Estimated: 5-7 days)

**Goal**: AI provider abstraction, classification, embeddings, feedback.

**Files to create**:
- `app/secadmin/ai/classifier.py`
- `app/secadmin/ai/provider_openai.py`
- `app/secadmin/ai/provider_ollama.py`
- `app/secadmin/ai/provider_none.py`
- `app/secadmin/ai/embeddings.py`

**Files to modify**:
- `app/secadmin/worker.py` — Integrate AI classification
- `app/config.py` — Add AI config fields
- `pyproject.toml` — Add openai, httpx

**Exit criteria**:
- [ ] All three providers implemented
- [ ] AI runs on observations, stores results
- [ ] Structured output parsing with Pydantic
- [ ] Embeddings stored in pgvector
- [ ] Similar-message query works
- [ ] Monitor-only enforced (AI "delete" becomes "review")
- [ ] Prompt injection tested
- [ ] Officer feedback loop works

---

### Phase 9 — Cases and Reporting (Estimated: 3-4 days)

**Goal**: Case management, note timeline, exports.

**Files to create**:
- (Most already created in Phase 1/5)
- `api/routers/cases.py` (already created in Phase 5)

**Files to modify**:
- `api/routers/cases.py` — Add report endpoints
- `api/routers/reports.py` — CSV/JSON generation

**Exit criteria**:
- [ ] Cases can be created from events
- [ ] Notes with edit history
- [ ] Timeline visualization
- [ ] Event-to-case linking
- [ ] CSV reports download
- [ ] Case JSON export

---

### Phase 10 — Security Hardening (Estimated: 3-5 days)

**Goal**: Production hardening, documentation, deployment scripts.

**Files to modify**:
- `docker-compose.yml` — Resource limits, health checks, secrets
- `Caddyfile` — TLS config
- `scripts/create_roles.sql` — Verified and tested
- `README.md` — Updated deployment docs
- `DEPLOYMENT.md` — Updated
- `.env.example` — Complete

**Exit criteria**:
- [ ] Separate PostgreSQL roles tested
- [ ] Rate limiting configured
- [ ] CSRF protection active
- [ ] Retention cleanup verified
- [ ] Backup strategy documented
- [ ] Security checklist complete
- [ ] Penetration-testing notes addressed

---

## 20. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| R1 | Telegram Bot API rate limits on `getChatMember` | Medium | High — bot may be temporarily blocked | Cache admin status with 5-min TTL; batch queries; respect `retry_after` |
| R2 | AI classification latency blocks worker pipeline | Medium | Medium — observation processing delayed | Parallel AI + deterministic classification; 30s timeout; fallback to deterministic-only |
| R3 | pgvector query performance degrades with scale | Low | Medium | Index on embeddings (IVFFlat); partition by date; archive old embeddings |
| R4 | Officer session token leaked | Low | Critical | HTTP-only cookies; CSRF; short expiry (24h); revocation on logout; audit logging |
| R5 | False positive flood overwhelms officers | Medium | High | Deterministic-only mode toggle; bulk status updates; AI confidence threshold adjustment |
| R6 | PostgreSQL outbox becomes bottleneck under high message volume | Low | Medium | Index on (status, created_at); FOR UPDATE SKIP LOCKED; periodic VACUUM; archive processed jobs |
| R7 | AdCleaner bot token compromised | Low | Critical | Rotate token; remove bot from groups; redeploy; audit all bot actions |
| R8 | Prompt injection through Telegram messages | Medium | High — AI outputs harmful content | Structured output parsing; no tool access; no SQL generation; input length limit; output validation |

---

## 21. Definition of Done

A phase is complete when:

1. **All code written** — Every file from the plan exists and is functional
2. **All migrations run** — Alembic migrations apply without errors
3. **All tests pass** — Existing + new tests pass
4. **Lint passes** — `ruff check` with zero errors
5. **Format passes** — `ruff format --check` with zero errors
6. **Docker builds** — All containers build without errors
7. **Docker Compose starts** — All services come up healthy
8. **Manual smoke test** — Key flows verified manually
9. **Documentation updated** — README/DEPLOYMENT reflects changes
10. **No critical regression** — Phase 0 fixes are verified to still work

---

## 22. MVP vs Deferred Features

### MVP (Phases 0-7)

| Feature | Phase | Rationale |
|---------|-------|-----------|
| Repository repairs | 0 | Prerequisite for everything |
| SecAdmin database models | 1 | Foundation |
| Member observation | 2 | Core user directory |
| Security observation producer | 3 | Core detection pipeline |
| SecAdmin worker | 4 | Background processing |
| SecAdmin API | 5 | Web access |
| SecAdmin Web UI | 6 | Human interface |
| Enforcement bridge | 7 | Action loop closure |

### Deferred (Phases 8-10 or later)

| Feature | Phase | Rationale |
|---------|-------|-----------|
| AI classification | 8 | Works without AI; AI enhances |
| Embedding similarity | 8 | AI-dependent |
| AI feedback loop | 8 | Requires deployed AI |
| Cases and reporting | 9 | Works with events only |
| Security hardening | 10 | Production polish |
| Attachment scanning | Ultimate | Separate subsystem |
| Threat intel feeds | Ultimate | External dependency |
| SIEM/SOAR integration | Ultimate | External dependency |
| Two-person approval | Ultimate | Low-frequency need |
| Emergency lockdown | Ultimate | Requires additional Telegram rights |
| Local AI server (Ollama) | Ultimate | Infrastructure cost |
| Private SecAdmin Telegram bot | Ultimate | Separate bot token |
| Backup service | Ultimate | Can use standard PG tooling |

---

## Appendix: Broad Exception Locations to Fix

| File | Line | Current | Fix |
|------|------|---------|-----|
| `app/services/moderation.py` | 110 | `except Exception` | Catch `aiogram.exceptions.TelegramAPIError`; log member status |
| `app/services/permissions.py` | 24 | `except Exception` | Catch `TelegramBadRequest`, `TelegramRetryAfter`; retry on 429 |
| `app/services/permissions.py` | 51 | `except Exception` | Same |
| `app/services/permissions.py` | 60 | `except Exception` | Same |
| `app/handlers/membership.py` | 32 | `except Exception` | Catch `TelegramForbiddenError`, `TelegramRetryAfter` |
| `app/handlers/membership.py` | 40 | `except Exception` | Same |
| `app/services/cleanup.py` | 18 | `except Exception` | Catch specific DB exceptions; use `logger.exception` |
