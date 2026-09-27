# Security Hardening Reference

Based on the session's VPS hardening steps for GreenCloud VPS (194.127.192.52).

## SSH Hardening

### Change SSH Port
```bash
# Edit sshd_config
sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
# Or add new port while keeping old for testing
echo "Port 2222" >> /etc/ssh/sshd_config

# Allow in firewall BEFORE restarting SSH
ufw allow 2222/tcp comment 'SSH new port'

# Test new port
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 uptime

# Then disable old port
ufw delete allow 22/tcp
sed -i 's/^Port 22$/#Port 22/' /etc/ssh/sshd_config
systemctl restart ssh
```

### Key-Only Authentication
```bash
# /etc/ssh/sshd_config
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin yes          # or prohibit-password
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
```

### Fail2Ban
```bash
# Already installed and running on aaPanel
# Check status
fail2ban-client status sshd

# Configuration: /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
```

## UFW Firewall Rules

### Default Policy
```bash
ufw default deny incoming
ufw default allow outgoing
ufw enable
```

### Rules Applied
| Port | Protocol | Source | Action | Description |
|------|----------|--------|--------|-------------|
| 2222 | TCP | Any | ALLOW | SSH (key-only) |
| 80 | TCP | Any | ALLOW | HTTP |
| 443 | TCP | Any | ALLOW | HTTPS |
| 26676 | TCP | 158.140.180.101 | ALLOW | aaPanel (admin IP only) |
| 5678 | TCP | Any | ALLOW | n8n |
| 3306 | TCP | Any | DENY | MySQL (blocked external) |
| 22 | TCP | Any | DENY | Old SSH port |

### Commands
```bash
# Allow specific IP to aaPanel
ufw allow from 158.140.180.101 to any port 26676 proto tcp comment 'aaPanel admin IP'

# Deny MySQL externally
ufw deny 3306
ufw deny 3306/tcp

# Delete rule by number
ufw status numbered
ufw delete <number>
```

## aaPanel Security

### Access Restriction
- **Port 26676**: Only your IP (158.140.180.101)
- **SSL**: Force HTTPS for panel access
- **2FA**: Enable in aaPanel settings if available

### Database Security
- MySQL root password reset via `--skip-grant-tables`
- Remote root access disabled (localhost only)
- Application users with minimal privileges per database

## Docker Security

### n8n Container
```bash
# Run with restricted permissions
docker run -d \
  --name n8n \
  --user 1000:1000 \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

### Volume Permissions
```bash
# Ensure n8n can write to its volume
chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data
```

## Telegram Bot Security

### Authorization
```javascript
// In n8n function node
const AUTHORIZED_CHAT_ID = 316228407;

if (chatId !== AUTHORIZED_CHAT_ID) {
  return [{json: {response: 'Unauthorized', chatId}}];
}
```

### Webhook Security
- Use secret token in webhook URL: `https://domain/webhook/telegram/webhook?secret=randomstring`
- Validate secret in n8n workflow before processing
- Set webhook with secret: `curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" -d url="https://domain/webhook/telegram/webhook?secret=XYZ"`

## Monitoring & Alerting

### Cron Job Output
```bash
# Log all cron output
0 2 * * * /root/backup_db.sh >> /var/log/backup.log 2>&1
0 */6 * * * /root/health_check.sh >> /var/log/health.log 2>&1
```

### Log Rotation
```bash
# /etc/logrotate.d/custom-scripts
/var/log/backup.log /var/log/health.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Incident Response

### SSH Brute Force
```bash
# Check failed attempts
grep "Failed password" /var/log/auth.log | tail -20

# Check banned IPs
fail2ban-client status sshd

# Unban if needed
fail2ban-client set sshd unbanip 1.2.3.4
```

### Suspicious Activity
```bash
# Check for unexpected processes
ps aux --sort=-%cpu | head -20

# Check network connections
ss -tulpn

# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"
```

## Backup & Recovery

### Critical Files to Backup
| File | Location | Frequency |
|------|----------|-----------|
| SSH keys | `/root/.ssh/`, `/home/*/.ssh/` | On change |
| n8n data | Docker volume `n8n_data` | Daily (via workflow) |
| aaPanel config | `/www/server/panel/data/` | Weekly |
| MySQL databases | `/root/backups/` | Daily |
| Firewall rules | `ufw status verbose > /root/ufw-backup.txt` | On change |
| SSH config | `/etc/ssh/sshd_config` | On change |

### Recovery Commands
```bash
# Restore UFW rules
ufw reset
ufw allow 2222/tcp
ufw allow from <YOUR_IP> to any port 26676
# ... rest of rules

# Restore SSH config
cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
systemctl restart ssh

# Restore n8n data
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest

# Restore MySQL
gunzip -c /root/backups/all_dbs_YYYY-MM-DD.sql.gz | mysql -u root -p
```

## Compliance Checklist

- [ ] SSH port changed from 22
- [ ] Password authentication disabled
- [ ] Root login key-only
- [ ] Fail2Ban active on SSH
- [ ] UFW default deny incoming
- [ ] aaPanel restricted to admin IP
- [ ] MySQL external access blocked
- [ ] n8n webhook HTTPS only
- [ ] Telegram bot authorized chat ID only
- [ ] Cron jobs logging to files
- [ ] Log rotation configured
- [ ] Backup tested (restore verified)
- [ ] SSH keys backed up off-site
- [ ] 2FA on aaPanel (if available)
- [ ] Server monitoring alerts configured