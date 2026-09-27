# Implementation Details — Session Transcript

## Original Session Context
This skill was created from a real-world session setting up Telegram + n8n automation on a GreenCloud VPS (Singapore, Ubuntu 22.04, aaPanel).

## VPS Details
- **IP**: 194.127.192.52
- **Provider**: GreenCloud (Singapore DC2)
- **Panel**: aaPanel 8.0.3 on port 26676
- **SSH**: Port 2222 (changed from 22), key-only auth
- **Docker**: n8n + temporal-postgres
- **Database**: MariaDB (aaPanel managed)

## Key Steps Performed

### 1. SSH Hardening
```bash
# Generate new key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vps_key

# Add public key to GreenCloud panel → VPS restart
# Verify in ~/.ssh/authorized_keys (3 keys total)
```

### 2. aaPanel Firewall Rules
- Port 22 → DENY (external firewall blocks anyway)
- Port 2222 → ALLOW (SSH new port)
- Port 26676 → ALLOW from specific IP only (aaPanel)
- Port 3306 → DENY (MySQL)
- Port 5678 → ALLOW (n8n)

### 3. MySQL Root Password Reset
```bash
systemctl stop mysqld
mysqld_safe --skip-grant-tables --skip-networking &
mysql -u root -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'RootPass123!@#'; FLUSH PRIVILEGES;"
pkill mysqld_safe
systemctl start mysqld
```

### 4. n8n Update & Data Migration
```bash
# Pull latest image
docker pull n8nio/n8n:latest

# Stop old container
docker stop n8n && docker rm n8n

# Find old volume with data
docker volume ls
# Found: db59cd31... (old) vs n8n_data (new empty)

# Copy data to new volume with correct permissions
cp -r /var/lib/docker/volumes/db59cd.../_data/* /var/lib/docker/volumes/n8n_data/_data/
chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data

# Start new container
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

### 5. Telegram Bot Setup
```bash
# 1. Create bot via @BotFather → get token
# 2. Chat bot → /start → get chat ID via getUpdates
# 3. Create helper scripts on VPS
# 4. Deploy n8n workflow via API
# 5. Set webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d url="https://n8n.domain/webhook/telegram/webhook"
```

### 6. Cron Jobs
```bash
crontab -l | cat - <<'EOF' | crontab -
0 2 * * * /root/backup_db.sh
0 */6 * * * /root/health_check.sh
@reboot sleep 30 && /root/telegram_notify.sh "🔄 Server Rebooted"
EOF
```

## n8n Workflow Structure

### Nodes
1. **Telegram Webhook** — POST /webhook/telegram/webhook
2. **Parse Command** — Function node: authorize chat ID, parse command
3. **Send Reply** — HTTP Request to Telegram sendMessage API

### Commands Handled
- `/start`, `/help` → Show menu
- `/status` → uptime, free, df -h
- `/backup` → trigger backup script
- `/health` → CPU, RAM, disk, Docker
- `/restart <service>` → systemctl restart
- `/logs <service>` → journalctl -u service

## API Key Management
- n8n API Key: Settings → API → Generate
- Used in curl headers: `X-N8N-API-KEY: <key>`
- Stored in workflow deployment scripts

## File Locations on VPS

| File | Path | Purpose |
|------|------|---------|
| telegram_notify.sh | /root/telegram_notify.sh | Send Telegram messages |
| backup_db.sh | /root/backup_db.sh | MySQL backup + notify |
| health_check.sh | /root/health_check.sh | System health + notify |
| telegram_workflow.json | /root/telegram_workflow.json | n8n workflow definition |

## Cron Environment Notes
- Cron runs with minimal PATH: `/usr/bin:/bin`
- Always use absolute paths in cron scripts
- Redirect output: `>> /var/log/backup.log 2>&1`
- Test with `run-parts --test /etc/cron.daily`

## Lessons Learned

1. **Always copy n8n volume data before updating** — `docker rm` loses data if not in named volume
2. **UFW rules persist across reboots** — but Docker manipulates iptables directly, allow in both
3. **GreenCloud external firewall** — port 22 blocked at provider level, not UFW
4. **aaPanel stores MySQL password in panel DB** — not in `/root/.my.cnf`
5. **Telegram webhook requires HTTPS** — n8n behind reverse proxy with valid SSL cert
6. **Chat ID format**: Private = positive, Groups = negative (`-100...`)
7. **n8n webhook path must match** — case sensitive, no trailing slash
8. **Markdown in Telegram** — escape `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`