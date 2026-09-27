# Rate Limits & Anti-Patterns per Platform

Known rate limits, quotas, and anti-patterns to avoid when using Agent Reach.

## General Principles

1. **Space requests 2-3 seconds apart** minimum
2. **Use burner accounts** for all cookie-based platforms
3. **Respect `Retry-After` headers** when present
4. **Monitor for ban signals**: 403, 429, "login required" on valid cookies, empty results
5. **Rotate cookies periodically** (weekly for heavy use, monthly for light use)

---

## Platform-Specific Limits

### Twitter/X (twitter-cli / OpenCLI)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Search | ~30 req/15min (unofficial) | Varies by account age/trust |
| User timeline | ~900 req/15min | Higher for own timeline |
| Tweet lookup | ~900 req/15min | Single tweet + replies |
| Feed | ~15 req/15min | Home timeline |

**Anti-patterns:**
- ❌ Rapid-fire search queries (triggers captcha/ban)
- ❌ Using main account (high ban risk)
- ❌ Data center IPs (VPS/Cloud) — use residential proxy
- ❌ Followers/following endpoints (heavily rate limited, ban risk)

**Best practice:** Use `twitter feed` and `twitter user-posts` (stable) over `twitter search` (unstable).

---

### Reddit (OpenCLI / rdt-cli)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Search | ~60 req/min | Via browser session |
| Subreddit browse | ~60 req/min | |
| Post read | ~60 req/min | |
| Comments | ~60 req/min | |

**Anti-patterns:**
- ❌ No zero-config path — must login
- ❌ Official API requires approval (rarely granted)
- ❌ Anonymous `.json` endpoints return 403

**Best practice:** Use OpenCLI on desktop (reuses browser session). For servers, use rdt-cli with cookie.

---

### 小红书 / XiaoHongShu (OpenCLI / xiaohongshu-mcp)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Search | ~30 req/min | Triggers captcha if exceeded |
| Note read | ~30 req/min | Requires xsec_token from search |
| Comments | ~20 req/min | |
| Feed | ~10 req/min | |

**Critical Constraints:**
- **xsec_token MANDATORY** — cannot use bare note_id. Must get full URL from search/feed first.
- Token expires quickly — re-search before each read if needed.
- High frequency → captcha → IP/account ban.

**Anti-patterns:**
- ❌ Using bare note_id to read (will fail)
- ❌ Batch reading without re-searching for fresh tokens
- ❌ Using main account
- ❌ xhs-cli (legacy, unstable, author moved to OpenCLI)

**Best practice:** 
1. Search → get results with full URLs
2. Wait 2-3s
3. Read note using full URL from step 1
4. Wait 2-3s before next operation

---

### Facebook (OpenCLI only)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Search | ~20 req/min | |
| Profile | ~20 req/min | |
| Feed | ~10 req/min | |
| Groups list | ~10 req/min | Only YOUR visible groups |

**Anti-patterns:**
- ❌ Expecting arbitrary group post access (NOT SUPPORTED)
- ❌ No Graph API access without Business Verification + App Review
- ❌ Groups API deprecated since 2018

**Limitation:** Only reads groups visible to YOUR logged-in account. No API for group posts/comments by group ID.

---

### Instagram (OpenCLI only)

| Operation | Limit | Notes |
|-----------|-------|-------|
| User search | ~30 req/min | NOT full-text post search |
| Profile | ~30 req/min | |
| User posts | ~20 req/min | |
| Explore | ~20 req/min | |

**Anti-patterns:**
- ❌ Expecting keyword search across posts (only user search)
- ❌ instaloader / unofficial APIs (401/429 unstable)

---

### LinkedIn (linkedin-mcp / Jina Reader)

| Operation | Limit | Notes |
|-----------|-------|-------|
| People search | ~10 req/min | MCP server |
| Profile | ~10 req/min | |
| Company | ~10 req/min | |
| Jobs search | ~10 req/min | |

**Fallback:** Jina Reader for public pages only (`curl r.jina.ai/linkedin.com/in/username`)

---

### Bilibili (bili-cli / search API)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Search | ~60 req/min | Public API, no auth |
| Video detail | ~60 req/min | |
| User space | ~30 req/min | |
| Hot ranking | ~10 req/min | |

**Anti-patterns:**
- ❌ **Using yt-dlp for Bilibili** — BLOCKED (412 risk control, no workaround)
- ❌ High-frequency requests from same IP

**Best practice:** bili-cli for full features, search API for lightweight needs.

---

### YouTube (yt-dlp)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Subtitle fetch | ~1000/day/IP | Generous but not unlimited |
| Video info | ~1000/day/IP | |
| Search | ~100/day/IP | Use sparingly |

**Anti-patterns:**
- ❌ Batch downloading hundreds of videos
- ❌ No JS runtime configured (sig extraction fails)

**Fix for Windows:**
```powershell
$cfg = 'C:\Users\pc\AppData\Roaming\yt-dlp\config'
New-Item -ItemType Directory -Force -Path (Split-Path $cfg) | Out-Null
if (-not (Test-Path $cfg) -or -not (Select-String -Path $cfg -Pattern '--js-runtimes' -Quiet)) {
  Add-Content -Path $cfg -Value '--js-runtimes node'
}
```

---

### Exa Search (mcporter + Exa MCP)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Web search | Generous free tier | No API key needed |
| Deep research | Lower quota | |

**Anti-patterns:**
- ❌ Not installing mcporter + Exa MCP (zero-config doesn't include this)

---

### V2EX (Public API)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Hot topics | Unlimited | No auth |
| Node topics | Unlimited | |
| Topic detail | Unlimited | |
| Replies | Unlimited | |
| User info | Unlimited | |

**Best practice:** Most generous platform. Add `User-Agent: agent-reach/1.0` header.

---

### RSS/Atom (feedparser)

| Operation | Limit | Notes |
|-----------|-------|-------|
| Feed parse | Unlimited | Local only |
| | | Respect server's `Cache-Control` / `ETag` |

---

### 小宇宙 / Xiaoyuzhou

| Operation | Limit | Notes |
|-----------|-------|-------|
| Search | ~20 req/min | MCP + Whisper |
| Episode + transcript | ~10 req/min | Transcription takes time |

---

### 雪球 / Xueqiu

| Operation | Limit | Notes |
|-----------|-------|-------|
| Stock quote | ~30 req/min | Cookie required |
| Search | ~20 req/min | |
| Hot posts | ~10 req/min | |

---

## Ban Recovery Checklist

If you hit a ban (403/429/login required on valid cookies):

1. **Stop immediately** — don't retry
2. **Wait 1-2 hours** (or 24h for severe)
3. **Rotate IP** (if using proxy)
4. **Clear cookies** and re-login with burner account
5. **Reduce frequency** — double your delay
6. **Check if platform changed API** — run `agent-reach doctor` to see if backend switched

---

## Monitoring Script

Run periodically to detect issues early:

```bash
# Quick health check
agent-reach doctor --json | jq '.channels[] | {platform: .name, backend: .active_backend, status: .status}'

# Or use the health check script from this skill
python scripts/health_check.py
```

---

## Summary Table

| Platform | Zero-Config? | Login Needed? | Ban Risk | Stable Backend |
|----------|--------------|---------------|----------|----------------|
| Web (Jina) | ✅ | ❌ | Zero | Jina Reader |
| YouTube | ✅ | ❌ | Low | yt-dlp |
| GitHub | ✅* | Optional | Zero | gh CLI |
| Bilibili | ✅ | ❌ | Low | bili-cli / search API |
| V2EX | ✅ | ❌ | Zero | Public API |
| RSS | ✅ | ❌ | Zero | feedparser |
| Exa Search | ⚠️ (needs mcporter) | ❌ | Zero | Exa MCP |
| Twitter | ❌ | ✅ | **HIGH** | twitter-cli / OpenCLI |
| Reddit | ❌ | ✅ | Medium | OpenCLI |
| 小红书 | ❌ | ✅ | **HIGH** | OpenCLI |
| Facebook | ❌ | ✅ | Medium | OpenCLI |
| Instagram | ❌ | ✅ | Medium | OpenCLI |
| LinkedIn | ❌ | ✅ | Low | linkedin-mcp / Jina |
| 小宇宙 | ❌ | ✅ | Low | xiaoyuzhou-mcp |
| 雪球 | ❌ | ✅ | Low | xueqiu-mcp |

*GitHub: public repos zero-config; private needs `gh auth login`