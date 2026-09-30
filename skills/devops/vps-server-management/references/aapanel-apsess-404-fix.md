# aaPanel Blank Dashboard / 404 — corrected model

## What the apsess middleware is

```python
# /www/server/panel/BTPanel/__init__.py
APSESS_PATH_RE = re.compile(r"^/((?:apsess_)+[A-Za-z0-9]{16,32})(/.*|$)")
wrap_apsess_middleware(app)   # KEEP ENABLED
```

A WSGI middleware over `app.wsgi_app`, so it runs **before** Flask routing:

- Path does **not** match the token regex → sets `bt.apsess_token = ''` and passes the request through unchanged. Not a rejection.
- Path matches → strips the token segment and sets `environ['PATH_INFO']` to the real path.

Any well-formed 16-32 char alphanumeric token is accepted; the token's value is not validated for path rewriting.

## Why you must not disable it

The panel frontend's axios interceptor prepends the token from `localStorage['apsess']` to every request, and that key is populated by a bootstrap script the same middleware injects into served HTML:

```js
const a = localStorage.getItem('apsess');
if (a) e.url = `/apsess_${a}${e.url}`;
```

So the browser calls `/apsess_<token>/system?action=…`. With the middleware commented out, none of those paths are rewritten → every API call 404s → dashboard renders with no data. Disabling it is a regression.

## Working configuration

```bash
echo '/' > /www/server/panel/data/admin_path.pl
chmod +x /www/server/panel/init.sh && /www/server/panel/init.sh restart
```

`admin_path` must stay `/`: the frontend's API calls are root-relative. A custom path also fails to hide anything, because the catch-all GET route `/<path:sub_path>` renders the index for any path.

## Verifying

```bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
H='https://<host>:<port>'

curl -k -s -A "$UA" -o /dev/null -w 'login   %{http_code}\n' "$H/login"
curl -k -s -A "$UA" -o /dev/null -w 'root    %{http_code}\n' "$H/"          # 302 -> /login when logged out
curl -k -s -A "$UA" -o /dev/null -w 'plain   %{http_code}\n' "$H/system?action=GetCpuInfo"
curl -k -s -A "$UA" -o /dev/null -w 'apsess  %{http_code}\n' "$H/apsess_abc123def456ghi789jkl012mno345pq/system?action=GetCpuInfo"

# route table as Flask registers it
cd /www/server/panel && ./pyenv/bin/python3 -c "from BTPanel import app; [print(r) for r in app.url_map.iter_rules()]"
```

Both the plain and `apsess_` forms must return 200. Unauthenticated `/system` and `/site` returning 302 to `/login` is correct behaviour — an injected bypass in `class/common.py`'s `local()` that returns early for those paths is a security hole and should be scoped to loopback.

The `-A` browser User-Agent is mandatory: `is_spider()` in `class/panelDefense.py` returns 404 for missing, short, or toolish UAs, which mimics a routing failure.

## When the backend is fine but the browser is empty

If both URL shapes return 200 and the browser still shows no data, the fault is client state, not the server:

- **VPS was rebooted.** The session secret is derived from `os.uname()` + `psutil.boot_time()` + a secret key. A reboot invalidates every existing session cookie and the stored `apsess` token → blank page or a login redirect loop. Test in incognito: if it renders there, the fix is clearing site data/cookies.
- **Malformed `localStorage['apsess']`.** Fails the regex, so prefixed URLs are not rewritten. Clear site data.
- **Cached old bundle** pointing at a previous port/path. Hard reload.

Decide with that test rather than continuing to patch server files.

## Editing panel Python over SSH

`sed "${line}a\"` collapses multi-line insertions into a single line — the escaped newlines do not survive the remote shell, and the panel then fails to start on a syntax error. `python3 -c "<multi-line>"` breaks the same way because the command is re-quoted through `bash -c`.

Use a script file:

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

Back up the file first and validate the syntax after: `./pyenv/bin/python3 -c "import ast; ast.parse(open('BTPanel/__init__.py').read())"`.
