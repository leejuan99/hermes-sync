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
- aaPanel dashboard blank / no data / no numbers after login
- aaPanel middleware/routing problems
- SSH access issues
- Server administration via SSH

## Core Knowledge

### aaPanel Blank Dashboard / 404 — Start Here

**Do NOT disable `ApsessPathMiddleware`.** This panel's frontend is built around it: the Vue axios interceptor reads `localStorage['apsess']` and prepends it to every call, so API requests go out as `/apsess_<32-char token>/<endpoint>`. The middleware does *not* require a token — on a path with no `apsess_` prefix it sets an empty token and passes the request straight through to Flask. Disabling it therefore blocks nothing that was working, and does break the dashboard: the prefixed URLs the frontend emits stop being rewritten to the real endpoint, every API call 404s, and the page renders with no data.

```python
# /www/server/panel/BTPanel/__init__.py
APSESS_PATH_RE = re.compile(r"^/((?:apsess_)+[A-Za-z0-9]{16,32})(/.*|$)")
wrap_apsess_middleware(app)   # KEEP ENABLED
```

**Diagnose in this order:**

1. Confirm the middleware is enabled: `grep -n 'wrap_apsess_middleware' /www/server/panel/BTPanel/__init__.py` — it must be uncommented.
2. Test with a browser User-Agent (see `is_spider()` below); without one every endpoint returns a misleading 404:
   ```bash
   UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
   curl -k -s -A "$UA" -o /dev/null -w '%{http_code}\n' https://<host>:<port>/login
   ```
3. Test both URL shapes — both must return 200:
   ```bash
   curl -k -s -A "$UA" -b "$COOKIES" 'https://<host>:<port>/system?action=GetCpuInfo'
   curl -k -s -A "$UA" -b "$COOKIES" 'https://<host>:<port>/apsess_<any 16-32 alnum>/system?action=GetCpuInfo'
   ```
   Any well-formed token works: the middleware rewrites the path without validating the token's value.
4. Enumerate the real route table before assuming a routing bug:
   ```bash
   cd /www/server/panel && ./pyenv/bin/python3 -c "from BTPanel import app; [print(r) for r in app.url_map.iter_rules()]"
   ```
5. If the backend checks out but the *browser* is still blank, it is client state — see the reboot pitfall in "Pitfalls to Avoid".

### Keep `admin_path` at the default (`/`)

This panel generation's frontend issues **root-relative** API calls (`/login`, `/system`, `/site`), so it only works when the panel is served at the root:

```bash
 echo '/' > /www/server/panel/data/admin_path.pl
chmod +x /www/server/panel/init.sh && /www/server/panel/init.sh restart
```

A custom `admin_path` does not hide the panel here anyway — the catch-all GET route `/<path:sub_path>` renders the index for any path, so `/anything/` still reaches the login page.

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
| **LSAPI_CHILDREN too high** | Per-site `LSAPI_CHILDREN=300`, *and* a global `PHP_LSAPI_CHILDREN=100` in `/usr/local/lsws/conf/httpd_config.conf` that every vhost inherits, let a traffic spike spawn ~100 PHP workers and OOM a small box | Cap both the global value and each site's `LSAPI_CHILDREN`. All sites share one pool, so taking a single site offline frees no RAM — see `references/server-memory-diagnostics.md` |

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

### admin_path: keep it at `/`

**Do not prefix panel routes with `admin_path`.** This panel's frontend issues root-relative API calls (`/login`, `/system`, `/site`), so a non-root `admin_path` is the very thing that breaks the dashboard. Set `admin_path` back to `/` (see "Keep `admin_path` at the default" above) rather than rewriting route decorators.

**Why prefixing the routes is wrong:** the decorators are registered at root (`/system`, `/site`, `/login`) precisely because the frontend calls them at root. Rewriting them to `admin_path + '/system'` makes the code agree with an `admin_path` that is itself the bug, and the API then 404s at whichever path the browser actually uses. Affected endpoints: `/system` (GetCpuInfo, GetMemInfo, GetDiskInfo), `/site` (get_site_list), `/login`.

### Path-prefix rewriting must happen at WSGI level, not in `before_request`

**`@app.before_request` cannot affect routing.** Flask resolves the URL in `RequestContext.match_request()` while the context is pushed, which happens *before* `before_request` handlers run. Assigning to `request.path` there changes only what the view body sees, never which view was selected — so a handler like:

```python
@app.before_request
def strip_admin_path_prefix():
    if request.path.startswith(admin_path + '/'):
        request.path = request.path[len(admin_path):]
```

looks right, compiles, restarts cleanly, and does nothing: the request was already matched, or already 404'd. This is the single biggest time sink when repairing aaPanel routing.

**Correct approach:** rewrite `PATH_INFO` in a WSGI middleware wrapping `app.wsgi_app`, which runs before Flask routes. `ApsessPathMiddleware` in the panel is exactly this pattern:

```python
class StripPrefixMiddleware:
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = (prefix or '').rstrip('/')

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if self.prefix and path.startswith(self.prefix + '/'):
            environ['PATH_INFO'] = path[len(self.prefix):] or '/'
        elif path == self.prefix:
            environ['PATH_INFO'] = '/'
        return self.app(environ, start_response)

app.wsgi_app = StripPrefixMiddleware(app.wsgi_app, admin_path)
```

Register it alongside `wrap_apsess_middleware(app)`. In practice it is usually unnecessary — leave `admin_path` at `/` and the frontend's root-relative calls match directly.

### GreenCloud Provider External Firewall (Critical Finding - Sep 2026)

**Issue:** GreenCloud VPS has an EXTERNAL firewall at the provider level that blocks ports EVEN when UFW/aaPanel allows them.

**Symptoms:**
- UFW shows port allowed: `ufw status | grep 26676` → ALLOW
- Panel works locally: `curl localhost:26676` → 200 OK
- External access fails: `curl domain.com:26676` → timeout/connection refused
- SSH port 22 blocked despite UFW allow (GreenCloud blocks by default)

**Root Cause:** GreenCloud's cloud firewall operates BEFORE traffic reaches the VPS. UFW rules are insufficient.

**Fix:** Must open ports in GreenCloud Control Panel:
1. Login to GreenCloud panel (where SSH keys are managed)
2. Network → Firewall / Security Groups
3. Add rule: Port 26676 (or 8888), TCP, Allow, 0.0.0.0/0
4. Save & Apply

**Workaround Used:** Changed aaPanel port from 26676 → 8888 (more standard, easier to remember)
```bash
echo 8888 > /www/server/panel/data/port.pl
/www/server/panel/init.sh restart
ufw allow 8888/tcp
```

**Key Lesson:** ALWAYS check provider-level firewall when UFW shows allowed but external access fails. This applies to ALL cloud providers (AWS Security Groups, DigitalOcean Firewalls, Linode Firewalls, Vultr Firewall, etc.).

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

## WP Toolkit: which sites appear in the list

The WP Toolkit page lists exactly the sites whose `project_type` is `WP2` — it queries the panel DB, it does not scan the filesystem:

```python
# /www/server/panel/class_v2/data_v2.py
query = public.S('sites').prefix('').where('project_type = ?', 'WP2').alias('s')
```

`project_type` of `PHP` makes a site invisible to the Toolkit no matter how WordPress-y it is. To add one:

```bash
cp /www/server/panel/data/default.db /www/server/panel/data/default.db.bak-$(date +%Y%m%d-%H%M%S)
sqlite3 /www/server/panel/data/default.db "UPDATE sites SET project_type='WP2' WHERE id IN (1,2,3);"
sqlite3 -header -column /www/server/panel/data/default.db 'SELECT id,name,project_type FROM sites;'
```

Then confirm every touched site still answers (`curl -s -o /dev/null -w '%{http_code}' -H "Host: <site>" http://127.0.0.1/` → 301/200).

State both side effects to the user before flipping:

- **The backup engine changes.** `class_v2/panel_backup_v2.py` branches on `project_type`: non-WP2 sites are archived as a plain `tar.gz`; WP2 sites go through `wp_toolkit.wpbackup(...).backup_full_get_data()` and record into `wordpress_backups` instead of `backup`. Any existing panel backup cron silently switches method.
- **Auto-login and type grouping need `wordpress_onekey`.** The list renders without a row; "log in to WP" and per-type filtering (which INNER JOINs that table) do not. Note `pass` there is stored in **plaintext**.

Mechanism, table shapes, diagnostics, and admin-credential rotation: `references/aapanel-wp-toolkit.md`.

**Auto-login replays a stored password.** `wordpress_onekey.pass` must equal the site's real WP admin password — reset the password in WordPress without updating that row and "log in to WP" fails silently, with no error. Rotate through WordPress itself (there is no wp-cli here) and verify before reporting:

```bash
cd /www/wwwroot/<site>
/www/server/php/83/bin/php -r "require 'wp-load.php'; wp_set_password('<NEW>', <ID>);"
/www/server/php/83/bin/php -r "require 'wp-load.php'; \$u=get_userdata(<ID>); echo wp_check_password('<NEW>', \$u->user_pass, <ID>) ? 'VALID' : 'INVALID';"
sqlite3 /www/server/panel/data/default.db "UPDATE wordpress_onekey SET pass='<NEW>' WHERE s_id=<site id>;"
```

Plaintext in that column is the feature, not a defect: the panel must replay the real password and WP keeps only a one-way hash, so it cannot be removed without giving up auto-login. `default.db` is `-rw------- root root` — verify that and state the exposure honestly (root/panel access required) rather than promising the secret is gone. `wp_set_password()` also invalidates that user's existing sessions.

## Verifying automated work actually runs

A script existing is not a script running. Before reporting any scheduled job healthy, check all three places a cron can live and read the newest artifact:

```bash
crontab -l
sqlite3 -header -column /www/server/panel/data/default.db 'SELECT id,name,type,where1,status FROM crontab;'
ls -lt /root/backups/ | head
```

The panel keeps its own cron rows in `default.db`, so a job can vanish from there while `/root/*.sh` still exists. If the newest artifact is older than the schedule, the job is dead regardless of what the script says.

Rebuild it so it fails loudly:

- Credentials in `/root/.my.cnf` (mode 600), invoked as `mysqldump --defaults-extra-file=/root/.my.cnf ...`. An inline `-p<password>` keeps "working" in the script while producing nothing the moment the DB password rotates — and `2>/dev/null` swallows the auth error that would have told you.
- Treat an empty or missing output file as failure (`[ -s "$OUT" ]`), delete the stub, notify.
- Prove it by running it once and validating the payload, e.g. `zcat <dump> | grep -c 'CREATE DATABASE'` should equal the number of databases on the server.

## Reporting to this user

- **Answer in casual Indonesian** (lo/gua). An English reply draws an immediate "what the fuck? indonesia pleasee" — never switch language, including in summaries.
- **Act, then report.** Batch independent probes into one command; a long unbroken chain of diagnostics with no interim answer reads as wasted time.
- **Separate verified from unverified, one line each.** A 200 from curl proves the backend, not that the browser renders data.
- **Lead with the risk you found**, not only the task that was asked. Silently repairing a dead backup while answering a cosmetic question is the highest-value outcome; say so first.

## Pitfalls to Avoid

1. **Never disable `wrap_apsess_middleware(app)`** — the frontend calls `/apsess_<token>/...`; disabling it 404s every API call and blanks the dashboard. It passes tokenless requests through, so it is not what is blocking you.
2. **`@app.before_request` cannot change routing.** URL matching happens during `ctx.push()`, before before_request runs. To strip or rewrite a path prefix use a WSGI middleware over `app.wsgi_app` (see the section above).
3. **`chmod +x /www/server/panel/init.sh` before restarting.** A "Permission denied" on `init.sh restart` is just a missing exec bit, not a broken panel.
4. **Always restart the panel after edits** — `chmod +x init.sh && ./init.sh restart`.
5. **Check Python syntax before restart** — `python3 -m py_compile file.py`.
6. **Clear Python cache after edits** — `find . -name '*.pyc' -delete && find . -name '__pycache__' -exec rm -rf {} +`.
7. **The panel socket must exist** — `/tmp/panel.sock`, with nginx `proxy_pass http://unix:/tmp/panel.sock;`.
8. **A VPS reboot invalidates every browser session.** The session secret is derived from `os.uname()` + `psutil.boot_time()` + a secret key, so a reboot changes it and all existing session cookies (plus the `apsess` token in `localStorage`) go stale → blank dashboard or a login redirect loop that looks like a server fault. Test in an incognito window first: if it renders there, the fix is "clear site data/cookies" on the user's browser, not a server change.
9. **Never leave an auth bypass in `local()`.** `/www/server/panel/class/common.py`'s `local()` can carry an injected early return such as `if request.path in ['/system','/site','/login']: return None`, which exposes unauthenticated API access on a public port. If one is present, scope it to loopback (`public.GetClientIp() in ('127.0.0.1', '::1')`) instead of leaving it open.
10. **Do not declare the dashboard fixed from API-level curls alone.** A 200 on `/system?action=GetCpuInfo` proves the backend, not that the browser renders data. Say explicitly what was verified and what was not.
11. **Never size memory from summed RSS.** RSS counts shared pages (OPcache, libraries) once per process, so a worker pool's RSS sum can be 2-3x its real footprint. Use PSS (`/proc/<pid>/smaps_rollup`) for per-component totals, and check the *available* column of `free -m` first — an inflated figure drives the wrong fix and has to be retracted. See `references/server-memory-diagnostics.md`.
12. **A restart recycles a process pool, it does not shrink it.** Restarting OpenLiteSpeed (or PHP-FPM) respawns the workers immediately and PSS lands back where it started. Do not present it as a memory saving; the durable levers are the worker ceiling and per-process `memory_limit`.
13. **Grep the panel source for a config key before hand-editing a generated config.** `grep -rn 'KEY' /www/server/panel/class/ /www/server/panel/class_v2/` returning nothing means the panel does not regenerate that file and a direct edit sticks; a hit means the change belongs in the panel DB or UI instead, and your edit will be silently overwritten.
14. **A batch script's exit status proves nothing about its individual writes.** A remote `bash` function called with a shifted positional argument fails silently on one target while the rest succeed, and the run still prints a tidy-looking table. Verify each written artifact against its own source of truth — read the row back, re-run the verifier — instead of trusting one green run.

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

## References
- `references/aapanel-404-debugging.md` — blank dashboard / 404 on the panel: the apsess middleware model, route-table inspection, session invalidation after reboot
- `references/aapanel-wp-toolkit.md` — WP Toolkit: which sites list (`project_type='WP2'`), `wordpress_onekey` / `wp_site_types` / `wordpress_backups` tables, admin-credential rotation, side effects of flipping a site
- `references/server-memory-diagnostics.md` — measuring real memory (PSS vs summed RSS), the single shared OpenLiteSpeed PHP pool, where `PHP_LSAPI_CHILDREN` lives, container memory limits and parking a service with `docker stop`

## Related Skills
- `github` - for version control of server configs
- `systematic-debugging` - for debugging methodology
- `terminal` - for SSH and command execution

## Version
1.2 - Added WordPress admin-credential rotation via `wp-load` (no wp-cli), the PSS-vs-RSS memory rule, and the shared OpenLiteSpeed PHP pool model (`references/server-memory-diagnostics.md`)
1.1 - Corrected the apsess / admin_path model (middleware must stay enabled; `before_request` cannot reroute); added WSGI-vs-before_request rule, reboot session invalidation, and remote multi-line edit pitfall