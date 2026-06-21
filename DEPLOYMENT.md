# AdCleaner — Deployment Manual

## 1. Architecture Overview

```
Internet
  │
  ├── Telegram Bot API
  │     │  (long polling)
  │     ▼
  │   ┌─────────────────────────┐
  │   │  bot (aiogram/Python)   │──┐
  │   │  Port: none (outbound)  │  │  public schema
  │   └─────────────────────────┘  │  (allowlists, logs, chats)
  │                                │
  ├── SecAdmin Web App            │
  │   │                           │
  │   ├── web (nginx + React) ────┤
  │   │   Port 80                 │
  │   │   /api/* → api:8000       │
  │   │   /*      → index.html    │
  │   │                           │
  │   └── api (FastAPI/Python) ───┤
  │       Port 8000               │  secadmin schema
  │       JWT auth                │  (events, indicators,
  │       REST API                │   cases, officers, ...)
  │                               │
  └── PostgreSQL ─────────────────┘
       Port 5432
       pgdata volume
```

Four containers: `postgres`, `bot`, `api`, `web`.

---

## 2. Telegram Bot Setup (BotFather)

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot` and follow the prompts:
   - **Bot name**: `AdCleaner` (or your preferred name)
   - **Bot username**: `adcleaner_bot` (must end in `bot`)
3. Save the HTTP API token. It looks like:
   ```
   1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
4. **Disable group privacy mode** (critical — bot won't see messages otherwise):
   ```
   /setprivacy
   ```
   Select your bot, then choose **Disable**.
5. **Set commands**:
   ```
   /setcommands
   ```
   Select your bot. Paste the group commands block:
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

---

## 3. Quick Start (Local Docker)

### Requirements
- Docker and Docker Compose (v2+)
- Git

### Steps

```bash
# 1. Clone
git clone <your-repo-url>
cd reklamatozalovchi

# 2. Configure
cp .env.example .env
```

Edit `.env` and set at minimum `BOT_TOKEN` and `API_SECRET_KEY`:
```
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
API_SECRET_KEY=generate-a-random-64-char-hex-secret
```

```bash
# 3. Build and start all services
docker compose up --build -d

# 4. Verify all containers are up
docker compose ps

# Expected:
# NAME                     STATUS
# reklamatozalovchi-bot    Up (healthy)
# reklamatozalovchi-api    Up (healthy)
# reklamatozalovchi-web    Up (healthy)
# reklamatozalovchi-postgres Up (healthy)
```

### 3.1 Initial Database Setup

Migrations run automatically on first start. You also need to create the database roles:

```bash
docker compose exec -T postgres psql -U adcleaner adcleaner < scripts/create_roles.sql
```

Then seed an admin officer to access the web dashboard:

```bash
docker compose exec bot python scripts/seed_officer.py --telegram-id YOUR_TELEGRAM_ID
```

### 3.2 Access the Web Dashboard

```
http://localhost
```

Log in with the seeded officer's Telegram ID and the password printed by `seed_officer.py`.

### 3.3 Adding the Bot to a Group

1. Open your bot's private chat in Telegram.
2. Tap the **Add to group** button, or search for the bot's username in your group.
3. Promote the bot to **administrator**.
4. Grant only the **Delete messages** permission.
5. The bot will confirm activation automatically.

### 3.4 Verify Bot is Working

Send `/status` in the group to see:
```
AdCleaner is Active.
Mode: Normal
Deleted today: 0
Trusted users and bots: 0
Trusted domains: 0
```

---

## 4. Configuration Reference

### 4.1 Environment Variables

| Variable | Required | Default | Used By | Description |
|---|---|---|---|---|
| `BOT_TOKEN` | **Yes** | — | bot | Telegram bot token from BotFather |
| `POSTGRES_PASSWORD` | **Yes** | `change_me` | all | PostgreSQL superuser password |
| `API_SECRET_KEY` | **Yes** | `change-me-in-production` | api | JWT signing secret (use `openssl rand -hex 32`) |
| `POSTGRES_DB` | No | `adcleaner` | all | PostgreSQL database name |
| `POSTGRES_USER` | No | `adcleaner` | all | PostgreSQL superuser |
| `DATABASE_URL` | No | *auto-built* | bot, api | Public schema connection string |
| `SECADMIN_DATABASE_URL` | No | *auto-built* | bot, api | SecAdmin schema connection string |
| `LOG_LEVEL` | No | `INFO` | all | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | No | `json` | all | `json` or `text` |
| `BOT_LANGUAGE` | No | `uz` | bot | Language code for bot messages |
| `DEFAULT_MODE` | No | `normal` | bot | Protection mode: `relaxed`, `normal`, `strict` |
| `DELETION_LOG_RETENTION_HOURS` | No | `24` | bot | Hours before deletion logs expire |
| `CLEANUP_INTERVAL_MINUTES` | No | `30` | bot | Minutes between cleanup cycles |
| `MESSAGE_EXCERPT_MAX_LENGTH` | No | `250` | bot | Max characters stored from deleted messages |
| `API_DEBUG` | No | `false` | api | Enable Swagger UI at `/docs` and `/redoc` |
| `API_SESSION_TTL_HOURS` | No | `24` | api | JWT session lifetime |
| `AI_ENABLED` | No | `false` | bot, api | Enable AI-powered content analysis |
| `AI_PROVIDER` | No | `openai` | bot | `openai` or `ollama` |
| `AI_MODEL` | No | `gpt-4o-mini` | bot | Model identifier |
| `AI_API_KEY` | — | — | bot | API key (required for OpenAI) |
| `AI_API_URL` | — | — | bot | Custom API endpoint URL |

### 4.2 Database Roles

The project uses four PostgreSQL roles with different permission levels:

| Role | Schema Access | Used By |
|---|---|---|
| `adcleaner_bot` | `public` (CRUD) | Bot service |
| `secadmin_api` | `secadmin` (all privileges) | API service |
| `secadmin_migrations` | `public` + `secadmin` (DDL) | Alembic migrations |
| `secadmin_reader` | `secadmin` (read-only) | Reporting / analytics |

Create them after first deploy:
```bash
docker compose exec -T postgres psql -U adcleaner adcleaner < scripts/create_roles.sql
```

### 4.3 SecAdmin Schema

All security/administration tables live in the `secadmin` schema:

| Table | Purpose |
|---|---|
| `security_observation_outbox` | Queue: raw Telegram updates awaiting processing |
| `security_events` | Detected security events (ad, phishing, spam) |
| `indicators` | Known IOCs: domains, URLs, usernames, wallets, etc. |
| `event_indicators` | Many-to-many link between events and indicators |
| `observed_users` | User profiles tracked across chats |
| `user_chat_profiles` | Per-chat user behavior stats |
| `user_observed_names` | Historical name/username changes |
| `member_risk_signals` | Risk signal observations per user+chat |
| `officers` | Admin dashboard users |
| `officer_sessions` | JWT session tokens |
| `officer_audit_logs` | Admin action audit trail |
| `cases` | Investigation cases |
| `case_events` | Events linked to a case |
| `case_notes` | Officer notes on cases |
| `enforcement_actions` | Telegram enforcement queue (delete, restrict, etc.) |
| `telegram_query_requests` | Telegram API query queue |
| `ai_model_registry` | Registered AI models |
| `ai_analysis_jobs` | AI analysis job queue |
| `ai_message_analyses` | AI analysis results |
| `message_embeddings` | Message text embeddings (for similarity search) |
| `ai_feedback` | Officer feedback on AI predictions |
| `system_health_events` | System health and error events |

The `message_embeddings` table stores vector embeddings for semantic similarity search. Currently the `embedding` column uses `TEXT` (base64-encoded). To enable native pgvector operations:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- Then migrate embedding column: ALTER COLUMN embedding TYPE vector(1536);
```

---

## 5. VPS Production Deployment

### Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 20 GB | 40 GB |
| OS | Ubuntu 22.04 / Debian 12 | Same |
| Docker | 24+ | Latest |
| Domain | Recommended | For web access |

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect

# Verify
docker --version
docker compose version
```

### Step 2: Clone and Configure

```bash
mkdir -p /opt/adcleaner
cd /opt/adcleaner

git clone <your-repo-url> .

# Configure
cp .env.example .env
nano .env
```

Set these values in `.env`:
```
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
POSTGRES_PASSWORD=<openssl rand -base64 32>
API_SECRET_KEY=<openssl rand -hex 32>
LOG_LEVEL=INFO
DEFAULT_MODE=normal
```

### Step 3: Start Services

```bash
docker compose up --build -d

# Verify all four containers
docker compose ps
```

### Step 4: Initial Setup

```bash
# Create database roles
docker compose exec -T postgres psql -U adcleaner adcleaner < scripts/create_roles.sql

# Seed an admin officer
docker compose exec bot python scripts/seed_officer.py \
  --telegram-id YOUR_TELEGRAM_ID \
  --role super_admin
```

### Step 5: Set Up HTTPS (Recommended)

The web service listens on port 80. For production, put a reverse proxy in front:

```bash
# Using Caddy (automatic HTTPS)
docker run -d \
  --name caddy \
  --network adcleaner_default \
  -p 443:443 -p 80:80 \
  -v caddy_data:/data \
  caddy:2 \
  caddy reverse_proxy --from your-domain.com --to web:80
```

### Step 6: Automatic Updates

```bash
echo "0 3 * * * root cd /opt/adcleaner && docker compose pull && docker compose up -d" > /etc/cron.d/adcleaner-update
```

---

## 6. Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f bot
docker compose logs -f api
docker compose logs -f web

# Last 100 lines
docker compose logs --tail=100 bot
```

### Restart a Service

```bash
docker compose restart bot
docker compose restart api
```

### Update

```bash
cd /opt/adcleaner
git pull
docker compose up --build -d
```

### Database Management

```bash
# Run migrations manually
docker compose exec bot alembic upgrade head

# Create a migration
docker compose exec bot alembic revision --autogenerate -m "description"

# Rollback
docker compose exec bot alembic downgrade -1

# Access database shell
docker compose exec postgres psql -U adcleaner adcleaner
```

### Backup

```bash
# Full database
docker compose exec postgres pg_dump -U adcleaner adcleaner > backup_$(date +%Y%m%d).sql

# SecAdmin schema only
docker compose exec postgres pg_dump -U adcleaner --schema=secadmin adcleaner > secadmin_$(date +%Y%m%d).sql
```

### Restore

```bash
cat backup_file.sql | docker compose exec -T postgres psql -U adcleaner adcleaner
```

### Run Tests

```bash
docker compose exec bot pytest -v
```

### Seed an Officer (CLI)

```bash
docker compose exec bot python scripts/seed_officer.py --help
```

---

## 7. Production Security Checklist

- [ ] `POSTGRES_PASSWORD` is strong (use `openssl rand -base64 32`)
- [ ] `API_SECRET_KEY` is strong (use `openssl rand -hex 32`)
- [ ] `BOT_TOKEN` is kept secret (never committed to git)
- [ ] `AI_API_KEY` is kept secret (if using OpenAI)
- [ ] PostgreSQL port is **not exposed** publicly (default: bound to `127.0.0.1`)
- [ ] `.env` file never committed to version control (already in `.gitignore`)
- [ ] Bot runs as non-root user (both Dockerfiles create dedicated users)
- [ ] API runs as non-root user (Dockerfile.api creates `secadmin` user)
- [ ] Firewall allows only necessary ports (80, 443, SSH)
- [ ] HTTPS is configured for the web dashboard
- [ ] Database roles use unique passwords (not `change_me`)
- [ ] Regular backups of the `pgdata` Docker volume
- [ ] Monitor logs for unusual activity
- [ ] API debug mode is **disabled** in production (`API_DEBUG=false`)
- [ ] JWT session TTL is reasonable (`API_SESSION_TTL_HOURS`)

---

## 8. Monitoring

### Health Endpoint

The API exposes a health check:
```bash
curl http://localhost:8000/health
```

### Container Health

```bash
docker compose ps
docker stats
```

### Log Patterns

| Log Message | Source | Meaning |
|---|---|---|
| `Starting polling...` | bot | Bot started normally |
| `Deleted message X in chat Y` | bot | Advertisement removed |
| `Failed to delete message X` | bot | Missing permission or already deleted |
| `SecAdmin database initialized` | api | API connected to secadmin schema |
| `POST /auth/login 200` | api | Successful officer login |
| `Unhandled error processing update` | bot | Unexpected error |

### API Endpoints (Swagger)

If `API_DEBUG=true`, visit:
- `http://your-domain.com/api/docs` — Swagger UI
- `http://your-domain.com/api/redoc` — ReDoc

---

## 9. Troubleshooting

### Bot does not respond to commands
```
docker compose logs bot | grep -i permission
```
**Fix**: Promote bot to admin with Delete messages permission.

### Bot cannot see messages
```
docker compose logs bot | grep -i "group privacy"
```
**Fix**: Send `/setprivacy` to BotFather, select bot, choose **Disable**.

### Database connection error
```
docker compose logs bot | grep -i database
```
**Fix**: Verify `DATABASE_URL` in `.env`. Wait for PostgreSQL health check.

### Web dashboard returns 502
```
docker compose logs api | tail
```
**Fix**: API may be down. Restart: `docker compose restart api`.

### Cannot log into web dashboard
```
docker compose exec postgres psql -U adcleaner adcleaner -c "SELECT telegram_id, role FROM secadmin.officers"
```
**Fix**: Ensure an officer record exists. Re-run `seed_officer.py`.

### "Connection is not available" errors
```
docker compose logs bot | grep -i connection
```
**Fix**: `docker compose restart bot`.

---

## 10. pgVector Setup (Optional)

The `message_embeddings` table stores vector embeddings for semantic similarity search. Currently the `embedding` column is `TEXT` (base64-encoded float array). To enable native pgvector operations:

```sql
-- 1. Install the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create a new column with the vector type (1536 = OpenAI embedding dimension)
ALTER TABLE secadmin.message_embeddings
  ADD COLUMN embedding_vec vector(1536);

-- 3. Backfill from existing text embeddings (when embeddings are stored)
-- UPDATE secadmin.message_embeddings
-- SET embedding_vec = embedding::vector(1536)
-- WHERE embedding IS NOT NULL;

-- 4. Create an IVFFlat index for approximate nearest neighbor search
CREATE INDEX idx_message_embeddings_vec
  ON secadmin.message_embeddings
  USING ivfflat (embedding_vec vector_cosine_ops)
  WITH (lists = 100);

-- 5. (Optional) Drop the text column once migration is complete
-- ALTER TABLE secadmin.message_embeddings DROP COLUMN embedding;
```
