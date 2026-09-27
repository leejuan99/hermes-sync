# aaPanel 404 Fix: APSESS_PATH_RE Middleware Root Cause

## Problem
aaPanel returns 404 for all requests to admin path (e.g., `/a83a1c60/`, `/login`) even though:
- Panel process is running
- Nginx proxy to unix socket works
- Route `/a83a1c60/` is registered in Flask app
- Nginx proxy to unix socket works

## Root Cause: APSESS_PATH_RE Middleware

The aaPanel has a **middleware** (`APSESSPathMiddleware`) that intercepts ALL requests at the WSGI level and requires a special `apsess_` token in the URL path.

### Middleware Pattern
```python
# /www/server/panel/BTPanel/__init__.py line 59
APSESS_PATH_RE = re.compile(r"^/((?:apsess_)+[A-Za-z0-9]{16,32})(/.*|$)")
```

### How It Works
1. Middleware wraps the Flask app: `app = wrap_apsess_middleware(app)`
2. Every request path is checked against `APSESS_PATH_RE`
3. Only URLs matching `^/apsess_<16-32 chars>/...` pass through
3. Requests without valid `apsess_` token return 404

### Exempt Paths (in `require_apsess()`)
Only these paths bypass the apsess check:
- `/login`, `/v2/login`, `/install`
- `/safe`, `/hook`, `/public`, `/down`
- `/userLang`, `/google/redirect`, `/google/callback`
- Static assets (handled by nginx directly)
- Plugin API exempt paths

**Custom admin paths like `/a83a1c60/` are NOT exempt!**

## Solution Options

### Option 1: Add Admin Path to Exempt List (Recommended)
Edit `/www/server/panel/BTPanel/__init__.py` in `require_apsess()` function:

```python
public_paths = (
    '/login', '/v2/login', '/install', '/safe', '/hook', '/public',
    '/down', '/userLang', '/google/redirect', '/google/callback',
    '/a83a1c60/',  # ADD THIS
    '/a83a1c60',   # AND THIS
)
```

### Option 2: Access with Token (Temporary)
Access via URL with apsess token:
```
https://server.smartmillionaire.co.id:26676/apsess_<YOUR_TOKEN>/a83a1c60/
```

### Option 3: Disable apsess Middleware (Works, Simpler for Dynamic IPs)
```python
# Comment out in /www/server/panel/BTPanel/__init__.py
# app = wrap_apsess_middleware(app)
```

**Used in session:** When user has dynamic IP (GreenCloud VPS), the token-based approach breaks on IP change. Disabling middleware is simpler and works reliably. Panel still requires login authentication.

## Debugging Commands
```bash
# Test if middleware is blocking
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/
# Expected 404 without token, 200 with valid token

# Check if middleware is active
grep -n "wrap_apsess_middleware" /www/server/panel/BTPanel/__init__.py

# Check require_apsess function
grep -n "require_apsess" /www/server/panel/BTPanel/__init__.py

# Test with apsess token
curl -k -s -o /dev/null -w '%{http_code}' "https://localhost:26676/apsess_<TOKEN>/a83a1c60/"
```

## Fix Applied
```bash
# Add admin path to exempt list
sed -i "s/public_paths = (/public_paths = (\n        '\/a83a1c60\/', '\/a83a1c60',/" /www/server/panel/BTPanel/__init__.py

# Restart aaPanel
/www/server/panel/init.sh restart
```

## Verification
```bash
# Test after fix
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/
# Should return 200

# Test login page
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/login
# Should return 200
```