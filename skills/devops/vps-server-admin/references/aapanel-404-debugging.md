# aaPanel: Blank Dashboard / 404 Diagnosis

## The Symptom

The user logs into aaPanel successfully, the page frame renders, but the dashboard shows **no numbers and no website data** — or login appears to succeed and then loops back. Websites and databases are fine; only the panel UI is empty.

## The Model: what `ApsessPathMiddleware` actually does

```python
# /www/server/panel/BTPanel/__init__.py
APSESS_PATH_RE = re.compile(r"^/((?:apsess_)+[A-Za-z0-9]{16,32})(/.*|$)")
wrap_apsess_middleware(app)   # KEEP ENABLED
```

It is a **WSGI** middleware wrapping `app.wsgi_app`. Per request it:

1. Matches `PATH_INFO` against `APSESS_PATH_RE`.
2. **No match** → sets `environ['bt.apsess_token'] = ''` and calls the app untouched. It does *not* reject the request.
3. **Match** → strips the token segment, sets `environ['PATH_INFO']` to the real path, records `bt.apsess_token`, and continues.

So a tokenless request like `/login` reaches Flask as `/login` either way. The middleware is not an access gate.

### Why disabling it breaks the dashboard

The frontend (Vue, `static/vite/...`) has an axios request interceptor roughly equivalent to:

```js
const a = localStorage.getItem('apsess');
if (a) e.url = `/apsess_${a}${e.url}`;
```

`localStorage['apsess']` is populated by a bootstrap `<script>` that the same middleware injects into served HTML (`_inject_apsess_html_bootstrap`). Result: **the browser calls every API as `/apsess_<token>/system?action=…`**. With the middleware commented out those URLs are never rewritten, so every API call 404s and the dashboard renders empty. Commenting out `wrap_apsess_middleware(app)` is a regression, not a fix.

Token value is not validated for path rewriting — any 16-32 char alphanumeric token works.

## Diagnosis order

```bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
H='https://<host>:<port>'

# 1. middleware enabled?
grep -n 'wrap_apsess_middleware' /www/server/panel/BTPanel/__init__.py

# 2. route table as Flask sees it
cd /www/server/panel && ./pyenv/bin/python3 -c "from BTPanel import app; [print(r) for r in app.url_map.iter_rules()]"

# 3. both URL shapes must be 200 (browser UA is mandatory — see below)
curl -k -s -A "$UA" -o /dev/null -w 'plain  %{http_code}\n' "$H/system?action=GetCpuInfo"
curl -k -s -A "$UA" -o /dev/null -w 'apsess %{http_code}\n' "$H/apsess_abc123def456ghi789jkl012mno345pq/system?action=GetCpuInfo"

# 4. page entry point
curl -k -s -A "$UA" -o /dev/null -w 'login  %{http_code}\n' "$H/login"
curl -k -s -A "$UA" -o /dev/null -w 'root   %{http_code}\n' "$H/"   # 302 -> /login when logged out is correct
```

### The User-Agent trap

`is_spider()` in `/www/server/panel/class/panelDefense.py` returns 404 for requests with a missing, short (<24 char), or toolish User-Agent (`curl`, `python`, `wget`, …). Testing the panel without `-A 'Mozilla/5.0 …'` produces 404s that look like routing or auth failures and send you down the wrong path. Always set a browser UA when probing aaPanel.

## Keep `admin_path` at `/`

The frontend's API calls are **root-relative**. A custom `admin_path` therefore breaks the dashboard, and it does not hide the panel anyway: the catch-all GET route `/<path:sub_path>` renders the index for any path.

```bash
echo '/' > /www/server/panel/data/admin_path.pl
chmod +x /www/server/panel/init.sh && /www/server/panel/init.sh restart
```

### If you genuinely need a hidden path

Rewrite `PATH_INFO` in a WSGI middleware over `app.wsgi_app`, never in `@app.before_request`: Flask resolves the URL in `RequestContext.match_request()` during `ctx.push()`, *before* before_request handlers run, so mutating `request.path` there never changes which view is selected.

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
```

## Browser-side causes (backend is healthy)

Before editing server files, rule these out — they present identically to a backend fault.

| Cause | Mechanism | Fix |
|-------|-----------|-----|
| **VPS rebooted** | Session secret = `os.uname()` + `psutil.boot_time()` + secret key. A reboot changes it → every existing session cookie and the `localStorage['apsess']` token are stale → blank / redirect loop | Test in incognito. If it renders, tell the user to clear site data + cookies |
| **Stale `localStorage['apsess']`** | A malformed token fails `APSESS_PATH_RE`, so the prefixed URL is not rewritten and every API call 404s | Clear site data, or reload via a valid `/apsess_<token>/…` URL |
| **Cached old bundle** | Old JS still points at a previous port/path | Hard reload (Ctrl+Shift+R) |

**Decision rule:** if `curl` with a browser UA returns 200 for both URL shapes but the user still sees an empty dashboard, the fault is client state. Do not keep patching server files.

## Instrumenting the real browser requests

The panel's nginx access log is `/dev/null` by default. To see what the browser actually requests:

```bash
sed -i 's|access_log /dev/null;|access_log /www/wwwlogs/panel_access.log;|g' /www/server/panel/webserver/conf/webserver.conf
chmod +x /www/server/panel/init.sh && /www/server/panel/init.sh restart
```

Note the config lives under `webserver/` (the panel's own nginx), not `nginx/`. If the file never appears, confirm the panel actually reloaded its webserver and that the directive landed inside the `server` block.

## Pitfall: leaving an auth bypass in `local()`

`/www/server/panel/class/common.py`'s `local()` is the per-request gate every panel route calls. A line such as:

```python
# Allow API requests to bypass local checks
if request.path in ['/system', '/site', '/login'] or request.path.startswith('/system/') ...:
    return None
```

is an injected backdoor exposing unauthenticated API access on a public port (stop services, read site lists). If you find one, scope it to loopback rather than leaving it open:

```python
if request.path in ['/system', '/site', '/login']:
    if public.GetClientIp() in ('127.0.0.1', '::1'):
        return None
```

Unpatched behaviour (correct) is a 302 redirect to `/login` for unauthenticated `/system` and `/site` requests.

## Editing panel Python over SSH

Multi-line insertion with `sed "${line}a\"` collapses into one line — the escaped newlines do not survive the remote shell, producing a syntax error and a panel that will not start. Write the edit as a script instead:

```bash
ssh ... "cat > /tmp/patch_panel.py << 'EOF'
with open('/www/server/panel/BTPanel/__init__.py') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'ANCHOR_TEXT' in line:
        lines.insert(i + 1, 'NEW LINE\n')
        break
with open('/www/server/panel/BTPanel/__init__.py', 'w') as f:
    f.writelines(lines)
EOF
python3 /tmp/patch_panel.py && rm /tmp/patch_panel.py"
```

`python3 -c "<multi-line>"` also fails here: the command is re-quoted through `bash -c` and the newlines break it. Always a script file.

Back up first (`cp BTPanel/__init__.py BTPanel/__init__.py.bak`) and verify after: `./pyenv/bin/python3 -c "import ast; ast.parse(open('BTPanel/__init__.py').read())"`.
