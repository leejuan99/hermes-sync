# aaPanel 404 Debugging Session - Detailed Reference

## Session Overview
**Date:** 2026-07-03 to 2026-07-04 (initial), 2026-08-29 (follow-up session)
**Issue:** aaPanel returning 404 on admin path `/a83a1c60/`
**Root Cause:** APSESS_PATH_RE middleware requiring `apsess_<token>/` prefix

## Root Cause Analysis

### The Middleware
```python
# /www/server/panel/BTPanel/__init__.py line 59
APSESS_PATH_RE = re.compile(r"^/((?:apsess_)+[A-Za-z0-9]{16,32})(/.*|$)")
```

This middleware wraps the Flask app via:
```python
wrap_apsess_middleware(app)  # Line 216
```

### Middleware Logic (`ApsessPathMiddleware`)
1. Extracts token from URL path: `/apsess_<token>/<real_path>`
2. Sets `environ['bt.apsess_token']` and rewrites `PATH_INFO`
3. If NO token found → sets empty token but **continues to app** (allows through)
4. BUT `check_apsess_path()` in `@app.before_request` **blocks** requests without valid token

### The `require_apsess()` Function
Determines which paths need apsess validation:
```python
def require_apsess():
    # Exempt paths:
    fixed_entry_paths = {'/', admin_path, route_path}
    if normalized_path in fixed_entry_paths:
        return False
    
    if is_safe_static_route_request():
        return False
    
    if is_plugin_api_exempt_request():
        return False
    
    # Public paths exempt:
    public_paths = (
        '/login', '/v2/login', '/install', '/safe', '/hook', '/public',
        '/down', '/userLang', '/google/redirect', '/google/callback'
    )
    for p in public_paths:
        if request.path == p or request.path.startswith(p):
            return False
    
    # Authenticated users: FORCE apsess validation
    return session.get('login', False)
```

**Critical Issue:** `/a83a1c60/` is NOT in `fixed_entry_paths` (it's `route_path` but with trailing slash mismatch) and NOT in `public_paths`.

### The Middleware Chain
1. Request comes in: `/a83a1c60/`
2. `ApsessPathMiddleware` - no token found → sets empty token, continues to app
3. `request_check()` runs → calls `check_apsess_path()`
4. `check_apsess_path()` → no token in environ → calls `handle_invalid_apsess()`
5. `handle_invalid_apsess()` → `require_apsess()` returns `True` (user logged in)
6. `handle_invalid_apsess()` → returns `abort(403)` → nginx shows 404

### Why Login Works Sometimes
The `/login` path IS in `public_paths` exempt list, so `require_apsess()` returns `False` for it.

### CRITICAL: Disabling Middleware Alone Is NOT Enough (Aug 2026 Discovery)
**Discovered in Aug 2026 session:** Simply commenting out `wrap_apsess_middleware(app)` does NOT fully disable apsess validation because:
- The `request_check()` @app.before_request handler (line 626) STILL calls `check_apsess_path()`
- `check_apsess_path()` does its OWN token validation independent of middleware
- Even with middleware disabled, `request_check()` will block requests without valid token for authenticated users

**To FULLY disable apsess validation:**
```bash
# Option 1: Comment out middleware wrap
sed -i 's|^wrap_apsess_middleware(app)|# wrap_apsess_middleware(app)|' /www/server/panel/BTPanel/__init__.py

# Option 2: ALSO modify check_apsess_path() to always return True
sed -i '7822,7850s/return True/return True  # DISABLED/' /www/server/panel/BTPanel/__init__.py
# Or edit check_apsess_path() to just: return True at the start

# Option 3: Add admin path to whitelist in require_apsess() (preferred)
# Edit /www/server/panel/BTPanel/__init__.py, in require_apsess():
public_paths = (
    '/a83a1c60/',
    '/a83a1c60',
    '/v2/a83a1c60/',
    '/v2/a83a1c60',
    # ... existing paths
)
```

### The `check_apsess_path()` Function (Line 7822)
```python
def check_apsess_path():
    apsess_token = build_apsess_url_token(request.environ.get('bt.apsess_token', ''))
    g.apsess_path_token = apsess_token
    g.apsess_verified = False
    
    if not apsess_token:
        return True  # ALLOWS through if no token (when middleware disabled)
    
    expected_token = get_apsess_url_token_from_session()
    if not expected_token or apsess_token != expected_token:
        return True  # ALLOWS through on mismatch (when middleware disabled)
    
    g.apsess_verified = True
    session['apsess_verified'] = True
    return True
```

**Key insight:** When middleware is disabled, `bt.apsess_token` is empty, so `check_apsess_path()` returns `True` immediately - this is why disabling middleware CAN work. But the 404 persisted due to OTHER issues (GetClientIp error, system freeze).

### Why 404 Persisted Even After Disabling Middleware (Aug 2026 Session)
1. **GetClientIp SyntaxError** - `request.remote_addr` was None causing AttributeError in error handler
2. **System freeze** - Load 151, Memory 92%, Swap 100% - VPS completely frozen
3. **Panel process restart issues** - bt.service showed "exited" but webserver processes alive
4. **uri_match regex** - Blocks paths not matching `^/[\w_\./\-]*$` pattern

## Fixes Applied

### 1. Fixed GetClientIp Syntax Error
**File:** `/www/server/panel/class/public/common.py` line 1113
**Issue:** Broken single-line function causing SyntaxError
**Fix:** Proper multi-line function with proper indentation

```python
def GetClientIp():
    from flask import request
    if request.remote_addr:
        ipaddr = request.remote_addr.replace("::ffff:", "")
        if not check_ip(ipaddr): return "Unknown IP address"
        return ipaddr
    return "Unknown IP address"
```

### 2. Re-enabled Middleware + Whitelist
```python
# Re-enable middleware
wrap_apsess_middleware(app)

# Add to public_paths in require_apsess():
public_paths = (
    '/a83a1c60/',
    '/a83a1c60',
    '/v2/a83a1c60/',
    '/v2/a83a1c60',
    # ... existing paths
)
```

### 3. uri_match Regex Understanding
The regex at line 512:
```python
uri_match = re.compile(
    r"(^/static/[\w_\./\-]+.(js|css|png|jpg|gif|ico|svg|woff|woff2|ttf|otf|eot|map)$|^/[\w_\./\-]*$)"
)
```
**Matches:** `/`, `/a83a1c60/`, `/login`, `/static/file.js`
**Blocks:** `/api/test`, paths with special chars not in `\w_\./\-`

This was NOT the cause of 404 in this case (admin path matched), but important to know.

## Testing Commands
```bash
# Test panel locally
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/a83a1c60/

# Test with token
curl -k -s -o /dev/null -w '%{http_code}' https://localhost:26676/apsess_<token>/a83a1c60/

# Check panel status
ps aux | grep -E 'BT-Panel|webserver'
ss -tlnp | grep 26676
```

## Key Files Modified
1. `/www/server/panel/class/public/common.py` - Fixed GetClientIp
2. `/www/server/panel/BTPanel/__init__.py` - Re-enabled middleware, added whitelist paths

## Lessons Learned (Aug 2026 Update)
1. **Always check middleware first** when seeing 404 on valid routes
2. **Check require_apsess() whitelist** for custom admin paths
3. **Test with Flask test client** to isolate middleware vs routing issues
4. **Check panel error logs** for AttributeError/500 errors
5. **Middleware wraps WSGI app** - affects all requests before Flask routing
6. **Disabling middleware is NOT enough** - request_check() still calls check_apsess_path()
7. **System resource exhaustion** (load 151, mem 92%, swap 100%) can freeze VPS completely
8. **Reboot via cloud provider panel** when SSH unresponsive
9. **Docker cache cleanup** critical: 7GB in /var/lib/docker
10. **Check bt.service status** - "exited" can be misleading (webserver may still run)