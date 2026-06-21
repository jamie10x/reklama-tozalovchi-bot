# Agent Handoff Notes

## Project State
- Repo: `/home/bot/bots/reklama-tozalovchi-bot`
- Branch: `codex/deploy-web-admin-nginx`
- Public admin URLs:
  - `https://meetus.uz/login`
  - `http://23.94.120.139:5001/login`
- Stack: Docker Compose with `postgres`, `bot`, `api`, `web`, `public-nginx`, `certbot`.
- The admin officer seeded on this VPS is Telegram ID `660089656`.

## Important Architecture
- Public bot tables live in the default schema, mainly `chats`, `allowed_entities`, `deletion_logs`.
- SecAdmin/admin-panel tables live in schema `secadmin`.
- API needs both DB sessions:
  - secadmin session for events, officers, users, indicators, activity.
  - public session for bot group records.
- Bot uses aiogram polling and starts:
  - `SecAdminWorker` for observation-to-event processing.
  - `EnforcementBridge` for admin-panel bot commands.

## Recent Feature Direction
- Telegram Bot API cannot fetch historical group messages. Message history starts only after the bot receives updates.
- Monitoring must be authorized: the bot must be present in the group and visible. For full message delivery in groups, BotFather privacy mode should be disabled.
- New activity concept:
  - Store metadata for future messages.
  - Store text based on group capture mode:
    - `metadata_only`
    - `flagged_only` default
    - `full_text`
- Suspicious detection should prioritize Uzbek Latin, Uzbek Cyrillic, English, and Russian.
- OSINT scope is Telegram-only unless explicitly expanded later.

## Useful Commands
```bash
docker compose ps
docker compose logs --tail=120 bot api web
docker compose up -d --build bot api web
docker compose exec -T api python -m compileall api app
docker compose build web
```

Authenticated API smoke test:
```bash
python - <<'PY'
from pathlib import Path
import json, subprocess
secret = next(line.split('=',1)[1] for line in Path('.env').read_text().splitlines() if line.startswith('API_SECRET_KEY='))
base='http://127.0.0.1:8000'
login = subprocess.run(['curl','-fsS','-X','POST',base+'/api/v1/auth/login','-H','Content-Type: application/json','-d',json.dumps({'telegram_id':660089656,'token':secret})],capture_output=True,text=True,check=True)
token=json.loads(login.stdout)['access_token']
for path in ['/api/v1/dashboard','/api/v1/groups','/api/v1/events?limit=5','/api/v1/activity/messages?limit=5']:
    res=subprocess.run(['curl','-fsS',base+path,'-H',f'Authorization: Bearer {token}'],capture_output=True,text=True,check=True)
    print(path, res.stdout[:600])
PY
```

## Safety / Product Constraints
- Do not build covert access or hidden surveillance.
- Do not claim the bot can fetch old history; it cannot.
- Admin panel commands execute only through Telegram Bot API permissions.
- If command results fail, show Telegram error text in `enforcement_actions.result`.

## Git Hygiene
- Do not revert user changes.
- Commit intentionally and push to `origin/codex/deploy-web-admin-nginx`.
