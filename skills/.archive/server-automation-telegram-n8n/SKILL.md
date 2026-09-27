---
name: server-automation-telegram-n8n
description: Build Telegram-controlled server automation using n8n workflows. Covers webhook setup, command parsing, server command execution, cron integration, and secure deployment patterns.
category: devops
tags: [telegram, n8n, automation, server-management, webhook, cron]
version: 1.0.0
---

# Server Automation with Telegram + n8n

## Overview
Complete pattern for controlling a VPS/server via Telegram bot commands, with n8n as the workflow engine. Provides 24/7 automation without requiring a local machine to stay online.

## Architecture

```
Telegram (Mobile) → Webhook → n8n (VPS) → Python SSH Executor (port 5679) → Server Commands → Response → Telegram
                    ↓
              Cron Jobs (VPS) → Scheduled Tasks → Telegram Notifications
```

### Component Details
- **n8n (port 5678)**: Workflow engine, webhook receiver
- **Python SSH Executor (port 5679)**: Lightweight HTTP server running on VPS to execute shell commands
- **Telegram Bot**: User interface via webhook
- **Cron Jobs**: Native cron on VPS for scheduled tasks

## Prerequisites
- VPS with Docker & n8n installed
- Telegram Bot (via @BotFather)
- Domain/subdomain pointing to n8n (for webhook HTTPS)
- SSH access to VPS (for initial setup)

## Quick Start

### 1. Create Telegram Bot
```bash
# Chat @BotFather → /newbot → get token
BOT_TOKEN="123456789:ABCdefGHI..."
```

### 2. Get Chat ID
```bash
# Chat your bot → send any message → run:
curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
# Extract "chat":{"id":XXXXXXXXX}
CHAT_ID="316228407"
```

### 3. Deploy Helper Scripts on VPS
```bash
# Copy scripts from templates/ to /root/
chmod +x /root/telegram_notify.sh /root/backup_db.sh /root/health_check.sh
```

### 4. Deploy Python SSH Executor on VPS
```bash
# Copy ssh_executor.py to /root/ on VPS
python3 /root/ssh_executor.py &
# Runs on port 5679
```

### 5. Create n8n Workflow via API
```bash
# Use the workflow template from templates/telegram-command-handler.json
# POST to n8n API with X-N8N-API-KEY header
```

### 6. Set Webhook
```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d url="https://your-n8n-domain/webhook/telegram/webhook"
```

### 7. Add Cron Jobs
```bash
crontab -l | cat - <<'EOF' | crontab -
0 2 * * * /root/backup_db.sh
0 */6 * * * /root/health_check.sh
@reboot sleep 30 && /root/telegram_notify.sh "🔄 Server Rebooted"
EOF
```

## Commands Supported

| Command | Description | Execution Method |
|---------|-------------|------------------|
| `/start`, `/help` | Show command menu | n8n reply only |
| `/status` | Server uptime, RAM, disk | Python SSH executor |
| `/backup` | Manual database backup | Python SSH executor |
| `/health` | Full health check (CPU, RAM, Docker) | Python SSH executor |
| `/restart <service>` | Restart systemd service | Python SSH executor |
| `/logs <service>` | Show recent service logs | Python SSH executor |

## Python SSH Executor (Port 5679)

**⚠️ CRITICAL: n8n's `ExecuteCommand` node has nodetype issues.** The actual node type is `n8n-nodes-base.executeCommand` (lowercase 'c'), NOT `n8n-nodes-base.ExecuteCommand`. Even with correct nodetype, n8n's ExecuteCommand node may fail to register in some versions.

**RECOMMENDED: Use a standalone Python HTTP server** (BaseHTTPRequestHandler, no Flask dependency) as a reliable fallback. This is what we actually used in production.

### Production-Ready Python SSH Executor (`/root/ssh_executor.py`)

```python
#!/usr/bin/env python3
"""
SSH Command Executor for n8n webhook
Runs as a simple HTTP server to execute shell commands
No Flask dependency - uses stdlib only
"""
import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y"
CHAT_ID = "316228407"

def send_telegram(chat_id, text):
    """Send message via Telegram Bot API"""
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data)
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram: {e}")

class SSHHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/ssh-command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                ssh_cmd = data.get('sshCmd', '')
                chat_id = data.get('chatId', CHAT_ID)
                
                if not ssh_cmd:
                    self.send_error(400, "No command provided")
                    return
                
                # Execute command
                result = subprocess.run(
                    ssh_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                output = result.stdout or result.stderr or "No output"
                if len(output) > 3500:
                    output = output[:3500] + "\n... (truncated)"
                
                # Send result via Telegram
                response_text = f"✅ *Command Result:*\n```\n{output}\n```"
                send_telegram(chat_id, response_text)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
                
            except subprocess.TimeoutExpired:
                send_telegram(chat_id, "❌ Command timed out (60s)")
                self.send_response(408)
                self.end_headers()
            except Exception as e:
                send_telegram(chat_id, f"❌ Error: {str(e)}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default log messages
        pass

if __name__ == '__main__':
    port = 5679  # Different from n8n's 5678
    server = HTTPServer(('0.0.0.0', port), SSHHandler)
    print(f"SSH Executor running on port {port}")
    server.serve_forever()
```

Run it:
```bash
# Run in background, survive terminal close
nohup python3 /root/ssh_executor.py > /root/ssh_executor.log 2>&1 & disown
# Or with systemd for production
```

### Why This Works Better Than n8n ExecuteCommand:
1. **No nodetype registration issues** - runs independently of n8n
2. **Zero dependencies** - stdlib only, no Flask/FastAPI needed
3. **Survives n8n restarts** - independent process
4. **Direct Telegram integration** - sends results back via Bot API
60s timeout protection
7. **Truncates long output** (3500 chars) to avoid Telegram limits
8. **Runs on port 5679** - no conflict with n8n (5678)

### n8n Workflow Integration

The n8n workflow calls this executor via HTTP:

```json
{
  "name": "Trigger SSH Executor",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://localhost:5679/ssh-command",
    "method": "POST",
    "jsonParameters": true,
    "bodyParametersJson": "{\n  \"sshCmd\": {{ $json.sshCmd }},\n  \"chatId\": {{ $json.chatId }}\n}"
  }
}
```

This architecture is **battle-tested** - the Python executor handles all shell execution while n8n handles Telegram webhook parsing and routing.

## Security

- **Authorization**: Only configured `CHAT_ID` can execute commands
- **Webhook**: HTTPS required (n8n behind reverse proxy with SSL)
- **SSH**: Use key-only auth, non-standard port, fail2ban
- **Firewall**: Restrict admin panels (aaPanel) to your IP only

## File Structure

```
/root/
├── telegram_notify.sh    # Send messages to Telegram
├── backup_db.sh          # mysqldump all DBs → gzip → retain 7 days
├── health_check.sh       # CPU, RAM, disk, Docker status
├── telegram_workflow.json # n8n workflow definition
```

## Cron Schedule

| Schedule | Task | Notification |
|----------|------|--------------|
| `0 2 * * *` | Backup all MySQL DBs | ✅ Telegram |
| `0 */6 * * *` | Health check | ✅ Telegram |
| `@reboot` | Startup notification | ✅ Telegram |

## Troubleshooting

### Webhook Not Receiving
```bash
# Check webhook status
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Verify n8n webhook endpoint
curl -X POST "https://your-domain/webhook/telegram/webhook" \
  -H "Content-Type: application/json" \
  -d '{"message":{"chat":{"id":YOUR_CHAT_ID},"text":"/help"}}'
```

### n8n Workflow Not Executing
- Check workflow is **Active** in n8n UI
- Verify webhook path matches (`telegram/webhook`)
- Check n8n logs: `docker logs n8n`

### Commands Not Working
- Verify `CHAT_ID` matches exactly in workflow function node
- Check bot token is correct in Send Reply node
- Ensure n8n can reach Telegram API (outbound HTTPS)

## References

- [references/implementation-details.md](references/implementation-details.md) — Full session transcript with VPS setup
- [references/security-hardening.md](references/security-hardening.md) — SSH, UFW, fail2ban, MySQL hardening steps
- [references/greencloud-specific.md](references/greencloud-specific.md) — GreenCloud VPS provider specifics (external firewall, IP restrictions)

## Templates

- [templates/telegram-command-handler.json](templates/telegram-command-handler.json) — n8n workflow definition
- [templates/telegram_notify.sh](templates/telegram_notify.sh) — Notification helper
- [templates/backup_db.sh](templates/backup_db.sh) — Database backup script
- [templates/health_check.sh](templates/health_check.sh) — Health check script

## Scripts

- [scripts/telegram_notify.sh](scripts/telegram_notify.sh) — Reusable notify function
- [scripts/backup_db.sh](scripts/backup_db.sh) — Backup with rotation
- [scripts/health_check.sh](scripts/health_check.sh) — Health metrics collector

## Pitfalls & Gotchas

1. **Webhook vs getUpdates**: Can't use both simultaneously. Delete webhook to use getUpdates.
2. **Chat ID Type**: Private chats = positive integer. Groups = negative (e.g., `-1001234567890`).
3. **Markdown Encoding**: Special chars in messages must be escaped for Markdown parse_mode.
4. **MySQL Password**: aaPanel doesn't store root password in plaintext. Reset via `--skip-grant-tables` if needed.
5. **SSH Port Change**: Update UFW rules *before* disabling old port, test new port first.
6. **n8n API Key**: Generate in n8n Settings → API. Required for programmatic workflow management.
7. **Cron Environment**: Cron runs with minimal PATH. Use absolute paths in scripts.
8. **Webhook URL**: Must be HTTPS with valid cert. Self-signed certs fail.
9. **⚠️ n8n ExecuteCommand Node Nodetype**: The actual node type is `n8n-nodes-base.executeCommand` (lowercase 'c'), NOT `n8n-nodes-base.ExecuteCommand` (capital C). Even with correct casing, this node may fail to register in some n8n versions. **Workaround**: Use standalone Python HTTP server (see Python SSH Executor section).
10. **n8n ExecuteCommand Node Registration**: Even with correct nodetype `n8n-nodes-base.executeCommand`, the node may fail with "Unrecognized node type" error. **Workaround**: Use standalone Python HTTP server as executor.
11. **GreenCloud External Firewall**: GreenCloud blocks ports at provider level. Must configure firewall rules in GreenCloud Control Panel, not just UFW.
12. **VNC Password Input**: In VNC console, password characters don't display when typing - this is normal Linux behavior, just type blindly and press Enter.
13. **aaPanel MySQL Password**: Not in `/root/.my.cnf`. Stored in panel database. Reset via `--skip-grant-tables` if needed.
14. **SSH Key Injection**: GreenCloud injects SSH keys via its SSH Keys panel, not just `authorized_keys`.
15. **n8n ExecuteCommand Nodetype Casing**: Must use `n8n-nodes-base.executeCommand` (lowercase 'c'), not `ExecuteCommand`.