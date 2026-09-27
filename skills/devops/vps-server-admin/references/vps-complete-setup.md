# VPS Complete Setup & Maintenance Reference

## Session Overview
**Date:** 2026-07-03 to 2026-07-04
**Scope:** Complete VPS setup, hardening, and service deployment

## Complete Setup Checklist

### 1. SSH Hardening
```bash
# Port 2222, key-only auth
Port 2222
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
```

**SSH Key Setup:**
```bash
# Generate key (once)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vps_key

# Copy public key to VPS
ssh-copy-id -p 2222 -i ~/.ssh/vps_key.pub root@194.127.192.52

# Or manually add to VPS
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 "
  mkdir -p ~/.ssh
  echo 'PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys
  chmod 600 ~/.ssh/authorized_keys
"
```

### 2. UFW Firewall Rules
```bash
# Enable UFW
ufw enable

# Allow required ports
ufw allow 2222/tcp    # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 26676/tcp   # aaPanel
ufw allow 5678/tcp    # n8n
ufw allow 5679/tcp    # n8n task broker (internal)

# Restrict aaPanel to specific IPs
ufw delete allow 26676/tcp
ufw allow from YOUR_IPv4 to any port 26676 proto tcp
ufw allow from YOUR_IPv6 to any port 26676 proto tcp

# Block MySQL external
ufw deny 3306/tcp

# Enable
ufw enable
```

### 3. SSH Hardening
```bash
# /etc/ssh/sshd_config
Port 2222
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
PermitEmptyPasswords no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# Restart SSH
systemctl restart sshd
```

### 3. aaPanel Configuration

#### Fix 404 Issue (APSESS Middleware)
**Root Cause:** APSESS middleware requires `apsess_<token>/` prefix

**Fix Options:**
1. Access with token: `https://domain:26676/apsess_<token>/admin_path/`
2. Disable middleware: Comment `wrap_apsess_middleware(app)` in `/www/server/panel/BTPanel/__init__.py`
3. Add to whitelist in `require_apsess()`:
```python
public_paths = (
    '/a83a1c60/',
    '/a83a1c60',
    '/v2/a83a1c60/',
    '/v2/a83a1c60',
    # ... existing paths
)
```

#### Fix GetClientIp Syntax Error
```bash
# File: /www/server/panel/class/public/common.py
def GetClientIp():
    from flask import request
    if request.remote_addr:
        ipaddr = request.remote_addr.replace("::ffff:", "")
        if not check_ip(ipaddr): return "Unknown IP address"
        return ipaddr
    return "Unknown IP address"
```

#### Panel Restart
```bash
chmod +x /www/server/panel/init.sh
/www/server/panel/init.sh restart
```

### 4. n8n Setup & Update

#### Initial Setup (Docker)
```bash
docker run -d --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

#### Update to Latest
```bash
docker pull n8nio/n8n:latest
docker stop n8n && docker rm n8n
docker run -d --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

#### Verify Version
```bash
docker exec n8n n8n --version
```

#### n8n API Workflow Creation
```bash
# Create workflow via API
curl -X POST 'https://n8n.domain.com/api/v1/workflows' \
  -H 'X-N8N-API-KEY: <API_KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Workflow Name","nodes":[...],"connections":{...}}'

# Activate workflow
curl -X POST 'https://n8n.domain.com/api/v1/workflows/<ID>/activate' \
  -H 'X-N8N-API-KEY: <API_KEY>'
```

### 5. Telegram Bot Integration

#### Create Bot
1. Message `@BotFather` on Telegram
2. `/newbot` → follow prompts
3. Save **Bot Token**: `8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y`

#### Get Chat ID
```bash
# Chat with bot, then:
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"
# Find "chat":{"id":316228407}
```

#### Send Message
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d chat_id="<CHAT_ID>" \
  -d text="Your message"
```

#### n8n Webhook Setup
1. Create workflow with Webhook node
2. Set webhook URL: `https://n8n.domain.com/webhook/telegram/webhook`
3. Set Telegram webhook:
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d url="https://n8n.domain.com/webhook/telegram/webhook"
```

#### n8n Workflow for SSH Commands
1. Webhook node → receives Telegram messages
2. IF node → check if command is SSH command
4. HTTP Request node → POST to `http://localhost:5679/ssh-command`
5. Python SSH executor on VPS port 5679 executes command
6. Returns result via Telegram

### 6. Cron Jobs (Auto-Run)

#### Add to Crontab
```bash
crontab -e
```

```cron
# Backup DB daily at 2 AM
0 2 * * * /root/backup_db.sh

# Health check every 6 hours
0 */6 * * * /root/health_check.sh

# Reboot notification
@reboot sleep 30 && /root/telegram_notify.sh "🔄 Server Rebooted\n$(date)\n✅ Server online"

# Cleanup cron
0 3 * * * find /tmp -name "tirith-install-*" -type d -mtime +1 -exec rm -rf {} \; 2>/dev/null
0 4 * * 0 find /www/wwwroot/*/wp-content/ai1wm-backups -type f -mtime +30 -delete 2>/dev/null
0 5 1 * * find /www/server/panel/logs -name "*.log" -mtime +30 -delete 2>/dev/null
```

#### Backup Script (/root/backup_db.sh)
```bash
#!/bin/bash
DATE=$(date +%F_%H-%M)
BACKUP_DIR="/root/backups"
mkdir -p ${BACKUP_DIR}

mysqldump -u root -pRootPass123!@# --all-databases --single-transaction --routines --triggers 2>/dev/null | gzip > ${BACKUP_DIR}/all_dbs_${DATE}.sql.gz

find ${BACKUP_DIR} -name "all_dbs_*.sql.gz" -mtime +7 -delete

/root/telegram_notify.sh "✅ Backup Database Selesai
📅 $(date)
📦 File: all_dbs_${DATE}.sql.gz
💾 Size: $(du -h ${BACKUP_DIR}/all_dbs_${DATE}.sql.gz | cut -f1)
📂 Lokasi: ${BACKUP_DIR}/"
```

#### Health Check Script (/root/health_check.sh)
```bash
#!/bin/bash
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8"%"}')
RAM_USED=$(free -h | awk '/Mem:/ {print $3}')
RAM_TOTAL=$(free -h | awk '/Mem:/ {print $2}')
DISK=$(df -h / | awk 'NR==2 {print $5}')
DOCKER=$(docker ps --format '{{.Names}}: {{.Status}}' | paste -sd ',' -)
UPTIME=$(uptime -p)

MSG="📊 Server Health Check
⏰ $(date)
⏱ Uptime: ${UPTIME}
🖥 CPU: ${CPU}
🧠 RAM: ${RAM_USED} / ${RAM_TOTAL}
💾 Disk: ${DISK} used
🐳 Docker: ${DOCKER}"

/root/telegram_notify.sh "${MSG}"
```

#### Telegram Notify Script (/root/telegram_notify.sh)
```bash
#!/bin/bash
BOT_TOKEN="8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y"
CHAT_ID="316228407"
MESSAGE="$1"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d text="${MESSAGE}" \
  -d parse_mode="Markdown" > /dev/null
```

### 6. Disk Cleanup (99% → 71%)

#### Identify Space Hogs
```bash
df -h /
du -h / --max-depth=1 | sort -hr | head -20
```

#### Clean Up
```bash
# Clean tirith-install temp files (15GB!)
rm -rf /tmp/tirith-install-*

# Clean WP backups
rm -rf /www/wwwroot/member.smartmillionaire.co.id/wp-content/ai1wm-backups/*

# Clean aaPanel logs
find /www/server/panel/logs -name "*.log" -mtime +7 -delete
```

#### Auto-Cleanup Cron
```cron
# Daily cleanup tirith-install
0 3 * * * find /tmp -name "tirith-install-*" -type d -mtime +1 -exec rm -rf {} \; 2>/dev/null

# Weekly WP backup cleanup
0 4 * * 0 find /www/wwwroot/*/wp-content/ai1wm-backups -type f -mtime +30 -delete 2>/dev/null

# Monthly aaPanel logs
0 5 1 * * find /www/server/panel/logs -name "*.log" -mtime +30 -delete 2>/dev/null
```

### 7. n8n Workflow for Telegram Bot Commands

#### Workflow Structure
```
Webhook (Telegram) → Parse Command → IF (is SSH?) → HTTP Request (localhost:5666789) → Send Reply
```

#### Commands Supported
| Command | Action |
|---------|--------|
| `/start` / `/help` | Show menu |
| `/status` | Server status (uptime, RAM, disk) |
| `/health` | Health check |
| `/backup` | Manual backup |
| `/restart <service>` | Restart service |
| `/logs <service>` | Show logs |

### 7. Monitoring & Alerts

#### Fail2Ban Status
```bash
fail2ban-client status sshd
# Currently banned: 7 IPs
# Total banned: 1665
```

#### Disk Monitoring
```bash
# Alert if > 80%
df -h / | awk 'NR==2 {gsub(/%/,"",$5); if ($5>80) print "ALERT: Disk at " $5 "%"}'
```

### 8. Quick Reference

| Task | Command |
|------|---------|
| SSH to VPS | `ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52` |
| Restart aaPanel | `/www/server/panel/init.sh restart` |
| Check aaPanel status | `ps aux | grep BT-Panel` |
| View aaPanel logs | `tail -50 /www/server/panel/logs/error.log` |
| Restart n8n | `docker restart n8n` |
| Check n8n logs | `docker logs n8n --tail 50` |
| Update n8n | `docker pull n8nio/n8n:latest && docker stop n8n && docker rm n8n && docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest` |
| Check disk space | `df -h /` |
| Check memory | `free -h` |
| View cron jobs | `crontab -l` |
| Edit cron | `crontab -e` |
| Test Telegram bot | `curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" -d chat_id="<CHAT_ID>" -d text="test"` |
| Check fail2ban | `fail2ban-client status sshd` |
| View UFW rules | `ufw status numbered` |

## Emergency Procedures

### Panel Won't Start
```bash
# 1. Check logs
tail -50 /www/server/panel/logs/error.log

# 2. Check Python syntax
python3 -m py_compile /www/server/panel/class/public/common.py

# 3. Clear cache
find /www/server/panel -name '*.pyc' -delete
find /www/server/panel -name '__pycache__' -exec rm -rf {} +

# 4. Restart
/www/server/panel/init.sh restart
```

### Can't Access Panel
```bash
# 1. Check if running
ps aux | grep BT-Panel
ss -tlnp | grep 26676

# 2. Check firewall
ufw status | grep 26676

# 3. Check nginx proxy
tail -30 /www/server/panel/webserver/logs/error.log

# 4. Test direct socket
curl -k -s -o /dev/null -w '%{http_code}' --unix-socket /tmp/panel.sock http://localhost/a83a1c60/
```

### Disk Full
```bash
# Find large files
du -h / --max-depth=1 | sort -hr | head -20

# Clean tmp
rm -rf /tmp/tirith-install-*

# Clean WP backups
rm -rf /www/wwwroot/*/wp-content/ai1wm-backups/*

# Clean logs
find /www/server/panel/logs -name "*.log" -mtime +7 -delete
```

## Version History
- 1.0 - Initial creation (aaPanel 404 fix)
- 1.1 - Added complete setup reference, n8n, Telegram, cron, disk cleanup