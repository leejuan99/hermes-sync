# VPS Disk Cleanup Procedure

## When to Run
- Disk usage > 90%
- After major deployments/updates
- Monthly maintenance

## Quick Check (Run First)
```bash
# Overall usage
df -h /

# Top 20 directories
du -h / --max-depth=2 2>/dev/null | sort -hr | head -20

# Journal size (often single largest consumer)
journalctl --disk-usage

# OpenLiteSpeed logs size
du -sh /usr/local/lsws/logs

# Docker system usage
docker system df
```

## Cleanup Steps (In Order)

### 1. Systemd Journal (often 3-4GB)
```bash
# Vacuum existing logs
journalctl --vacuum-size=500M --vacuum-time=7d

# Set permanent limit
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/99-limit.conf << 'EOF'
[Journal]
SystemMaxUse=500M
SystemMaxFileSize=100M
SystemKeepFree=1G
MaxRetentionSec=7day
EOF
systemctl restart systemd-journald
```

### 2. Docker Cleanup
```bash
# Dangling images & build cache (until 24h)
docker image prune -a -f --filter "until=24h"
docker builder prune -a -f --filter "until=24h"

# Unused volumes
docker volume prune -f

# Verify
docker system df
```

### 3. aaPanel Logs
```bash
# Panel logs > 7 days
find /www/server/panel/logs -type f -name "*.log" -mtime +7 -delete
find /www/server/panel/logs -type f -name "*.log.*" -delete

# Nginx/OLS access logs rotated > 7 days
find /www/wwwlogs -type f -name "*.log" -mtime +7 -delete
find /www/wwwlogs -type f -name "*.log.*" -delete
```

### 4. OpenLiteSpeed Logs (CRITICAL - often 10-15GB)
```bash
find /usr/local/lsws/logs -type f -name "*.log" -mtime +7 -delete
find /usr/local/lsws/logs -type f -name "*.log.*" -mtime +7 -delete
```

### 5. Root Cache Directories
```bash
# Go build cache (often largest)
rm -rf /root/.cache/go-build

# Electron cache
rm -rf /root/.cache/electron

# Playwright cache
rm -rf /root/.cache/ms-playwright

# Node-gyp cache
rm -rf /root/.cache/node-gyp

# UV cache
rm -rf /root/.cache/uv

# Pip cache
rm -rf /root/.cache/pip
```

### 6. Hermes Cache (keep config)
```bash
find /root/.hermes -type f -name "*.db" -delete
find /root/.hermes -type f -name "*.log" -delete
find /root/.hermes -type d \( -name cache -o -name audio_cache -o -name plugins \) -exec rm -rf {} +
```

### 7. WP Uploads (check for duplicates)
```bash
# Check for large video duplicates in WP uploads
find /www/wwwroot/*/wp-content/uploads -type f -size +100M -printf "%s %p\n" | sort -rn | head -20
```

### 8. APT Cache
```bash
apt-get clean && apt-get autoclean -y
```

## Verify Cleanup
```bash
df -h /
journalctl --disk-usage
du -sh /usr/local/lsws/logs
docker system df
```

## Prevention: Auto-Cleanup Cron
```bash
crontab -e

# Journal vacuum daily (500MB limit + 7d retention)
0 2 * * * journalctl --vacuum-size=500M --vacuum-time=7d 2>/dev/null

# Docker cleanup daily
0 3 * * * docker image prune -a -f --filter "until=24h" && docker builder prune -a -f --filter "until=24h" 2>/dev/null

# OpenLiteSpeed logs weekly
0 4 * * 0 find /usr/local/lsws/logs -name "*.log" -mtime +7 -delete 2>/dev/null
find /usr/local/lsws/logs -name "*.log.*" -mtime +7 -delete 2>/dev/null

# Root caches daily
0 3 * * * rm -rf /root/.cache/go-build /root/.cache/electron /root/.cache/ms-playwright /root/.cache/node-gyp /root/.cache/uv /root/.cache/pip 2>/dev/null

# Hermes cache daily
0 3 * * * find /root/.hermes -type f -name "*.db" -delete; find /root/.hermes -type f -name "*.log" -delete; find /root/.hermes -type d \( -name cache -o -name audio_cache -o -name plugins \) -exec rm -rf {} + 2>/dev/null

# aaPanel logs monthly
0 5 1 * * find /www/server/panel/logs -name "*.log" -mtime +30 -delete 2>/dev/null

# WP backups weekly
0 4 * * 0 find /www/wwwroot/*/wp-content/ai1wm-backups -type f -mtime +30 -delete 2>/dev/null
```