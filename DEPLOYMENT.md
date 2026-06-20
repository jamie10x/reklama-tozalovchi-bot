# AdCleaner Bot — Deployment Manual

## 1. Telegram Bot Setup (BotFather)

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

## 2. Quick Start (Local Docker)

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

Edit `.env` and set your bot token:
```
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

```bash
# 3. Build and start
docker compose up --build -d

# 4. Check logs
docker compose logs -f bot
```

You should see:
```
INFO:app.main:Starting polling...
```

### Adding to a group

1. Open your bot's private chat in Telegram.
2. Tap the **Add to group** button, or search for the bot's username in your group.
3. Promote the bot to **administrator**.
4. Grant only the **Delete messages** permission.
5. The bot will confirm activation automatically.

### Verify

Send `/status` in the group to see:
```
AdCleaner is Active.
Mode: Normal
Deleted today: 0
Trusted users and bots: 0
Trusted domains: 0
```

---

## 3. VPS Production Deployment

### Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 1 core | 2 cores |
| RAM | 512 MB | 1 GB |
| Disk | 10 GB | 20 GB |
| OS | Ubuntu 22.04 / Debian 12 | Same |
| Docker | 24+ | Latest |
| Domain (optional) | — | For webhook future use |

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

# Copy project files to the server (using git or scp)
git clone <your-repo-url> .

# Configure
cp .env.example .env
nano .env
```

Set these values in `.env`:
```
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
POSTGRES_PASSWORD=<generate-a-strong-password>
LOG_LEVEL=INFO
DEFAULT_MODE=normal
```

Generate a strong password:
```bash
openssl rand -base64 32
```

### Step 3: Start Services

```bash
# Pull images and build
docker compose up --build -d

# Verify both containers are running
docker compose ps

# Expected output:
# NAME                   IMAGE                      STATUS
# reklamatozalovchi-bot  reklamatozalovchi-bot      Up (healthy)
# reklamatozalovchi-postgres postgres:16-alpine       Up (healthy)
```

### Step 4: Verify Bot is Running

```bash
# Check bot logs
docker compose logs -f bot
```

Expected final log line:
```
2026-06-20T12:00:00+0000 [INFO] app.main: Starting polling...
```

### Step 5: Set Up Automatic Updates (Optional)

Create a cron job or systemd timer for automatic updates:

```bash
# As root, create /etc/cron.d/adcleaner-update
echo "0 3 * * * root cd /opt/adcleaner && docker compose pull && docker compose up -d" > /etc/cron.d/adcleaner-update
```

---

## 4. Maintenance Commands

### View Logs

```bash
# All logs
docker compose logs -f

# Bot logs only
docker compose logs -f bot

# Database logs
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail=100 bot
```

### Restart Bot

```bash
docker compose restart bot
```

### Update Bot

```bash
cd /opt/adcleaner
git pull
docker compose up --build -d
```

### Database Management

```bash
# Run migrations manually
docker compose exec bot alembic upgrade head

# Create a migration snapshot
docker compose exec bot alembic revision --autogenerate -m "description"

# Rollback one step
docker compose exec bot alembic downgrade -1

# Access database shell
docker compose exec postgres psql -U adcleaner adcleaner
```

### Backup Database

```bash
docker compose exec postgres pg_dump -U adcleaner adcleaner > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
cat backup_file.sql | docker compose exec -T postgres psql -U adcleaner adcleaner
```

### Run Tests

```bash
docker compose exec bot pytest -v
```

### Cleanup Old Logs

Logs are cleaned automatically every 30 minutes (configurable via `CLEANUP_INTERVAL_MINUTES`). Deletion logs older than 24 hours are removed (configurable via `DELETION_LOG_RETENTION_HOURS`).

---

## 5. Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | **Yes** | — | Telegram bot token from BotFather |
| `DATABASE_URL` | No | `postgresql+asyncpg://adcleaner:change_me@postgres:5432/adcleaner` | PostgreSQL connection string |
| `POSTGRES_DB` | No | `adcleaner` | PostgreSQL database name |
| `POSTGRES_USER` | No | `adcleaner` | PostgreSQL user |
| `POSTGRES_PASSWORD` | **Yes** | `change_me` | PostgreSQL password (must be strong in production) |
| `LOG_LEVEL` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DEFAULT_MODE` | No | `normal` | Default protection mode: `relaxed`, `normal`, `strict` |
| `DELETION_LOG_RETENTION_HOURS` | No | `24` | Hours before deletion logs expire |
| `CLEANUP_INTERVAL_MINUTES` | No | `30` | Minutes between cleanup cycles |
| `MESSAGE_EXCERPT_MAX_LENGTH` | No | `250` | Max characters stored from deleted messages |

---

## 6. Production Security Checklist

- [ ] `POSTGRES_PASSWORD` is strong (use `openssl rand -base64 32`)
- [ ] `BOT_TOKEN` is kept secret (never committed to git)
- [ ] PostgreSQL port is **not exposed** publicly (default: bound to `127.0.0.1:5432`)
- [ ] `.env` file never committed to version control (already in `.gitignore`)
- [ ] Bot runs as non-root user (Dockerfile creates `adcleaner` user)
- [ ] Firewall allows only necessary ports (SSH, HTTP/HTTPS if using webhooks)
- [ ] Regular backups of the `pgdata` Docker volume
- [ ] Monitor logs for unusual activity

---

## 7. Monitoring

### Health Check

The bot uses long polling, so it has a persistent connection to Telegram. You can monitor:

```bash
# Process health
docker compose ps

# Resource usage
docker stats

# Bot responsiveness (sends a message from another account and checks)
```

### Log Monitoring

Watch for these log patterns:

| Log Message | Meaning | Action |
|---|---|---|
| `Starting polling...` | Bot started normally | — |
| `Deleted message X in chat Y` | Advertisement removed | — |
| `Failed to delete message X` | Missing permission or already deleted | Check admin permissions |
| `Error during log cleanup` | DB issue | Check database connection |
| `Could not verify your identity` | Anonymous admin tried config | Normal behavior |
| `Unhandled error processing update` | Unexpected error | Check logs for details |

### Alerting (Optional)

For production, consider:
- Using a monitoring service like Uptime Kuma, Grafana, or Prometheus
- Setting up healthcheck pings to a monitoring endpoint
- Using Telegram's own API to send alerts to a private admin group

---

## 8. Upgrading from Polling to Webhooks

The project is structured so webhooks can replace polling with minimal changes.

1. Set a domain and obtain an SSL certificate (e.g., via Let's Encrypt).
2. Add a reverse proxy (Caddy, Nginx) in `docker-compose.yml`.
3. Replace `dp.start_polling(bot)` with:
   ```python
   webhook_url = f"https://yourdomain.com/webhook/{config.bot_token}"
   await bot.set_webhook(webhook_url)
   await dp.start_webhook(webhook_url, host="0.0.0.0", port=8080)
   ```
4. Update your reverse proxy to forward `/webhook/{token}` to the bot container.

---

## 9. Troubleshooting

### Bot does not respond to commands

```
docker compose logs bot | grep -i permission
```

**Cause**: Bot is not an administrator or lacks Delete messages permission.
**Fix**: Promote to admin with Delete messages permission.

### Bot cannot see messages

```
docker compose logs bot | grep -i "group privacy"
```

**Cause**: Bot privacy mode is enabled in BotFather.
**Fix**: Send `/setprivacy` to BotFather, select bot, choose **Disable**.

### Database connection error on startup

```
docker compose logs bot | grep -i database
```

**Cause**: PostgreSQL not ready or connection URL wrong.
**Fix**: Verify `DATABASE_URL` in `.env`. Wait for PostgreSQL health check.

### "Connection is not available" errors

```
docker compose logs bot | grep -i connection
```

**Cause**: PostgreSQL restarted or out of connections.
**Fix**: Restart the bot container: `docker compose restart bot`.

### Bot crashes on edited messages

```
docker compose logs bot | grep ERROR
```

**Cause**: Normally handled gracefully in the code. Check the specific error.
**Fix**: Review the error and file an issue if needed.

---

## 10. Reference Architecture

```
Internet
  │
  ├── Telegram Bot API
  │     │  (long polling or webhook)
  │     ▼
  │   Bot Container (Python + Aiogram)
  │     │
  │     ├── Detection Engine (rule-based scoring)
  │     ├── Database Access (async SQLAlchemy)
  │     │     │
  │     │     ▼
  │     │   PostgreSQL (persistent volume)
  │     │
  │     └── Logging (stdout via Docker)
  │
  └── Administrators (Telegram clients)
        │  (commands via Telegram)
        ▼
      Group Chat
```
