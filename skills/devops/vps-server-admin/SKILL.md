---
name: vps-server-admin
category: devops
version: 1.0
description: VPS Server Administration - aaPanel management, SSH hardening, 404/500 debugging
---

# VPS Server Administration - aaPanel Management

## Overview
Class-level skill for managing VPS servers, particularly aaPanel-based servers. Covers SSH access, aaPanel configuration, common issues (404, 500 errors), middleware troubleshooting, and SSH-based server management.

## Triggers
- User needs to manage VPS/aaPanel server
- aaPanel 404/500 errors
- SSH access issues
- aaPanel middleware/routing problems
- Server administration via SSH

## Core Knowledge

### aaPanel 404 Root Cause: APSESS Middleware
**Root Cause:** aaPanel has a middleware (`APSESS_PATH_RE`) that requires ALL URLs to have an `apsess_<token>/` prefix. URLs without this token return 404.

```python
# /www/server/panel/BTPanel/__init__.py line 59
APSESS_PATH_RE = re.compile(r"^/((?:apsess_)+[A-Za-z0-9]{16,32})(/.*|$)")
```

**Affected URLs:**
- `/a83a1c60/` → 404 (no apsess_ prefix)
- `/login` → 404 (blocked by middleware)
- `/apsess_<token>/a83a1c60/` → WORKS

### Solutions for aaPanel 404

#### Option 1: Access with Token (Immediate)
```bash
# Get token from panel logs or generate
# Format: https://domain:port/apsess_<token>/admin_path/
https://server.domain.com:26676/apsess_<token>/a83a1c60/
```

#### Option 2: Disable Middleware (Permanent)
```bash
# Edit /www/server/panel/BTPanel/__init__.py
# Comment out line ~216:
# wrap_apsess_middleware(app)
# →
# # wrap_apsess_middleware(app)
```

#### Option 3: Add Path to Whitelist
```bash
# Edit /www/server/panel/BTPanel/__init__.py
# In require_apsess() function, add to public_paths:
public_paths = (
    '/a83a1c60/',
    '/a83a1c60',
    '/v2/a83a1c60/',
    '/v2/a83a1c60',
    # ... existing paths
)
```

### Common aaPanel Issues & Fixes

| Issue | Fix |
|-------|-----|
| 404 on admin path | Add path to `require_apsess()` whitelist OR disable middleware |
| 500 Internal Server Error | Check `/www/server/panel/logs/error.log` |
| Login page not loading | Check middleware, SSL config, port 26676 |
| BT-Task fails to start | Check Python syntax in `/www/server/panel/class/public/common.py` |
| Panel won't restart | Check `init.sh` permissions, kill existing processes |

### OpenLiteSpeed/WordPress 500 Errors

| Issue | Root Cause | Fix |
|-------|------------|-----|
| 500 on WordPress sites | LSAPI_CHILDREN limit reached | Increase `LSAPI_CHILDREN` and `maxConns` in vhost config |
| 500 on panel access | `is_spider()` blocks suspicious User-Agent | Use proper User-Agent header or disable `is_spider()` check |
| Database connection error | MySQL socket mismatch | Create symlink: `ln -sf /tmp/mysql.sock /var/run/mysqld/mysqld.sock` |
| PHP-FPM not responding | Stuck LSPHP processes | `pkill -9 -f lsphp && /www/server/panel/init.sh restart` |

### `is_spider()` User-Agent Blocking (Critical Finding)

**Root Cause:** The `panelDefense.py` `is_spider()` function in `/www/server/panel/class/panelDefense.py` blocks requests with:
- Missing User-Agent header
- Short User-Agent (< 24 chars)
- Suspicious User-Agent (curl, python, requests, wget, etc.)

**Impact:** Requests from curl, python scripts, automated tools return 404/500 even when panel is working.

**Test with proper User-Agent:**
```bash
curl -k -s -o /dev/null -w '%{http_code}' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  https://localhost:26676/a83a1c60/
```

**Fix Options:**
1. **Use proper User-Agent** (recommended for testing)
2. **Disable `is_spider()` check** in `panelDefense.py` - comment out the `is_spider()` call in `login()` function
3. **Add User-Agent to allowed list** in `is_scripter()` function

**Discovered in Session:** The `login()` function in `/www/server/panel/BTPanel/__init__.py` (line 2710) calls `is_spider()` and returns 404 if it returns `True`:
```python
def login():
    if public.is_spider(): return abort(404)
    # ... rest of login logic
```

This affects ALL panel routes including admin path, login page, and API endpoints when accessed with suspicious User-Agent.

**Also Affects WordPress Sites:** The `is_spider()` function is called via `public.is_spider()` and affects any WordPress site using aaPanel's panelDefense module. Member site 500 errors were partly caused by this when accessed via curl/test clients.

### LSAPI_CHILDREN Limit (500 Errors)

**Symptom:** `[UID:1000][PID] Reached max children process limit: 20, extra: 6, current: 26, busy: -1, please increase LSAPI_CHILDREN.`

**Fix:** Edit vhost config for affected site:
```bash
# Edit /www/server/panel/vhost/openlitespeed/detail/<site>.conf
# Change:
#   env                     LSAPI_CHILDREN=20
#   maxConns                20
# To:
#   env                     LSAPI_CHILDREN=100
#   maxConns                100

# Then restart:
/www/server/panel/init.sh restart
```

### MySQL Socket Mismatch

**Symptom:** PHP CLI `mysqli_sql_exception: No such file or directory` when connecting to `localhost`, but `127.0.0.1` works.

**Root Cause:** PHP CLI expects MySQL socket at `/var/run/mysqld/mysqld.sock` but aaPanel MariaDB creates it at `/tmp/mysql.sock`.

**Fix:**
```bash
mkdir -p /var/run/mysqld
ln -sf /tmp/mysql.sock /var/run/mysqld/mysqld.sock
# Test:
php -r '$mysqli = new mysqli("localhost", "user", "pass", "db"); echo $mysqli->connect_errno ? "Fail" : "OK";'
```

### Crashed MySQL Table Repair

**Symptom:** WordPress shows "Error establishing a database connection" but MySQL is running. PHP-FPM/LSPHP logs show:
```
Table './database_name/table_name' is marked as crashed and last (automatic?) repair failed
```

**Root Cause:** MyISAM tables can become crashed due to unclean shutdown, disk full, or hardware issues. The `wplo_options` table is particularly prone to this in WordPress.

**Diagnosis:**
```bash
# Check MySQL error log
tail -100 /usr/local/lsws/logs/stderr.log | grep -i "crashed\|repair failed"

# Or check directly in MySQL
mysql -u user -p database -e "CHECK TABLE table_name;"
```

**Fix - Repair Single Table:**
```bash
mysql -u db_user -p'password' database_name -e "REPAIR TABLE table_name;"
# Example for wplo_options:
mysql -u thegamec_wp632 -p'p1SyK6A2!)' thegamec_wp632 -e "REPAIR TABLE wplo_options;"
```

**Fix - Repair All Tables in Database:**
```bash
mysql -u db_user -p'password' database_name -e "SHOW TABLES;" | tail -n +2 | while read table; do
  echo "Repairing $table..."
  mysql -u db_user -p'password' database_name -e "REPAIR TABLE \`$table\`;"
done
```

**Prevention:**
1. Set up automated table checks: `mysqlcheck --auto-repair --all-databases`
2. Monitor disk space - full disk causes table corruption
3. Ensure proper shutdown procedures
4. Consider converting MyISAM to InnoDB (more crash-resistant):
   ```sql
   ALTER TABLE table_name ENGINE=InnoDB;
   ```

**WordPress Specific:** The `wplo_options` table is heavily used by WordPress transients and autoload options. High-traffic sites with many plugins (Fluent CRM, Fluent Forms, etc.) are more prone to this issue.

### SSH Hardening (Standard)
```bash
# Port 2222, key-only auth
Port 2222
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
```

### UFW Firewall Rules
```bash
# Allow SSH (2222), HTTP/HTTPS, aaPanel (26676), n8n (5678)
ufw allow 2222/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 26676/tcp
ufw allow 5678/tcp
# Deny MySQL external
ufw deny 3306
```

### Fix GetClientIp for Proxy Headers (Critical)

**Problem:** aaPanel's `GetClientIp()` function crashes with `AttributeError: 'NoneType' object has no attribute 'replace'` when `request.remote_addr` is `None` (happens behind nginx/OpenLiteSpeed proxy).

**File:** `/www/server/panel/class/public/common.py`

**Fix:** Replace the function to handle `None` and check proxy headers:

```python
def GetClientIp():
    from flask import request
    # Handle case when remote_addr is None (Unix socket / proxy)
    if request.remote_addr is None:
        # Try to get from proxy headers
        ipaddr = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or '127.0.0.1'
    else:
        ipaddr = (request.remote_addr or "127.0.0.1").replace('::ffff:', '')
    if not check_ip(ipaddr): return 'Unknown IP address'
    return ipaddr
```

**After edit:** Restart panel:
```bash
pkill -9 -f "BT-Panel" 2>/dev/null
pkill -9 -f "BT-Task" 2>/dev/null
cd /www/server/panel
nohup /www/server/panel/pyenv/bin/python3 BT-Panel > /dev/null 2>&1 &
nohup /www/server/panel/pyenv/bin/python3 BT-Task > /dev/null 2>&1 &
```

## SSH Access Patterns

### Standard Connection
```bash
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52
```

### Run Commands Remotely
```bash
# Single command
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 "command"

# Multiple commands
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 "
  cd /www/server/panel
  /www/server/panel/init.sh restart
"
```

### File Transfer
```bash
# Upload
scp -P 2222 -i ~/.ssh/vps_key local_file root@194.127.192.52:/remote/path

# Download
scp -P 2222 -i ~/.ssh/vps_key root@194.127.192.52:/remote/file ./local/
```

## Debugging Workflow

### 1. Check Panel Status
```bash
ps aux | grep -E 'BT-Panel|webserver'
ss -tlnp | grep 26676
```

### 2. Check Logs
```bash
# Panel error log
tail -50 /www/server/panel/logs/error.log

# Nginx/OpenLiteSpeed error log
tail -30 /www/server/panel/webserver/logs/error.log

# LSPHP stderr log (critical for 500 errors)
tail -100 /usr/local/lsws/logs/stderr.log | grep -i 'LSAPI_CHILDREN\|Reached max\|crashed\|repair failed'
```

### 3. Check Database Issues
```bash
# Check for crashed tables in MySQL error log
tail -100 /usr/local/lsws/logs/stderr.log | grep -i "crashed\|repair failed"

# Check specific database
mysql -u db_user -p'password' database_name -e "CHECK TABLE table_name;"

# Repair crashed table
mysql -u db_user -p'password' database_name -e "REPAIR TABLE table_name;"

# Repair all tables in database
mysql -u db_user -p'password' database_name -e "SHOW TABLES;" | tail -n +2 | while read table; do
  mysql -u db_user -p'password' database_name -e "REPAIR TABLE \`$table\`;"
done
```

### 4. Test Direct Socket
```bash
# Test panel socket directly
curl -k -s -o /dev/null -w '%{http_code}' --unix-socket /tmp/panel.sock http://localhost/a83a1c60/
```

### 5. Check Middleware Status
```bash
grep -n 'wrap_apsess_middleware' /www/server/panel/BTPanel/__init__.py
grep -n 'require_apsess' /www/server/panel/BTPanel/__init__.py
```

### 6. Restart Services
```bash
chmod +x /www/server/panel/init.sh
/www/server/panel/init.sh restart
```

### 7. Check LSAPI_CHILDREN Limits (for 500 errors)
```bash
# Check stderr.log for limit warnings
tail -f /usr/local/lsws/logs/stderr.log | grep -i 'LSAPI_CHILDREN\|Reached max'

# Check vhost config
grep -A5 'extprocessor' /www/server/panel/vhost/openlitespeed/detail/<site>.conf
```

## Pitfalls to Avoid

1. **Don't disable middleware without whitelist** - breaks panel access
2. **Always restart panel after config changes** - `init.sh restart`
3. **Check Python syntax before restart** - `python3 -m py_compile file.py`
4. **Clear Python cache after edits** - `find . -name '*.pyc' -delete && find . -name '__pycache__' -exec rm -rf {} +`
5. **Check panel socket exists** - `/tmp/panel.sock` must exist
5. **Verify nginx proxy config** - ensure `proxy_pass http://unix:/tmp/panel.sock;`

## Quick Reference Commands

```bash
# Full restart sequence
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 "
  cd /www/server/panel
  /www/server/panel/init.sh restart
  sleep 5
  curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/
"

# Test panel locally
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/login

# Test external access
curl -k -s -L -o /dev/null -w '%{http_code} -> %{redirect_url}' https://server.domain.com:26676/a83a1c60/

# Check panel logs for errors
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 "tail -20 /www/server/panel/logs/error.log"
```

## Related Skills
- `github` - for version control of server configs
- `systematic-debugging` - for debugging methodology
- `terminal` - for SSH and command execution

## Version
1.0 - Initial creation based on aaPanel 404 debugging session