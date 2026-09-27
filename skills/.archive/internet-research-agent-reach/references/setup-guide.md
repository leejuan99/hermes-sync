# Agent Reach Setup Guide

Detailed setup instructions for each login-backed platform.

## Prerequisites

```bash
# Core tools (installed by agent-reach install)
pip install agent-reach
agent-reach install --env=auto

# For OpenCLI (desktop browser login reuse)
# 1. Install Chrome extension: https://chromewebstore.google.com/detail/opencli/...
# 2. pipx install opencli
pipx install opencli

# For mcporter (MCP gateway for Exa, LinkedIn, etc.)
npm install -g mcporter
```

---

## Twitter/X Setup

### Option A: twitter-cli (Recommended for search)

**Install:**
```bash
pipx install twitter-cli
```

**Authentication (Cookie-based):**
1. Login to twitter.com in Chrome
2. Install Cookie-Editor extension
3. Export cookies for twitter.com/x.com
4. Find `auth_token` and `ct0` values
5. Set as environment variables:
   ```bash
   export TWITTER_AUTH_TOKEN="your_auth_token_here"
   export TWITTER_CT0="your_ct0_here"
   ```
   Or add to `~/.agent-reach/config.yaml`:
   ```yaml
   twitter:
     auth_token: "your_auth_token"
     ct0: "your_ct0"
   ```

**Verify:**
```bash
twitter search "test" -n 1
```

> ⚠️ **Use burner account** — Twitter aggressively bans accounts using API/CLI tools.

### Option B: OpenCLI (Desktop, no cookie handling)

**Prerequisites:**
- Chrome browser
- OpenCLI Chrome extension installed
- Logged into twitter.com/x.com in Chrome

**Usage:**
```bash
opencli twitter search "query" -f yaml
```

---

## Reddit Setup

### Option A: OpenCLI (Desktop, browser login) — Preferred

**Prerequisites:**
- Chrome + OpenCLI extension
- Logged into reddit.com in Chrome

**Usage:**
```bash
opencli reddit search "query" -f yaml
```

### Option B: rdt-cli (Server/Legacy)

**Install:**
```bash
pipx install 'git+https://github.com/public-clis/rdt-cli.git'
```

**Login:**
```bash
rdt login  # Opens browser for OAuth
# Or for headless: manually write cookie to ~/.config/rdt-cli/cookie.json
```

**Verify:**
```bash
rdt search "test" --limit 1
```

> ⚠️ **No zero-config path** — anonymous API blocked. Must use login.

---

## 小红书 / XiaoHongShu Setup

### Option A: OpenCLI (Desktop) — Preferred

**Prerequisites:**
- Chrome + OpenCLI extension
- Logged into xiaohongshu.com in Chrome (scan QR in app)

**Usage:**
```bash
opencli xiaohongshu search "query" -f yaml
```

### Option B: xiaohongshu-mcp (Server, QR login)

**Setup:**
```bash
mcporter config add xiaohongshu https://mcp.xiaohongshu/mcp
```

**First run (QR login):**
```bash
mcporter call 'xiaohongshu.check_login_status()' --timeout 120000
mcporter call 'xiaohongshu.get_login_qrcode()' --timeout 120000
# Scan QR with 小红书 app
```

**Verify:**
```bash
mcporter call 'xiaohongshu.search_feeds(keyword: "test")' --timeout 120000
```

> ⚠️ **First run downloads ~150MB headless browser** — allow 2+ minutes.
> ⚠️ **xsec_token mandatory** — always use full URL from search results.

---

## Facebook Setup

**Only Option: OpenCLI (Desktop)**

**Prerequisites:**
- Chrome + OpenCLI extension
- Logged into facebook.com in Chrome

**Usage:**
```bash
opencli facebook search "query" -f yaml
opencli facebook groups --limit 20 -f yaml
```

> ⚠️ **Groups limitation:** Only reads groups visible to YOUR account. No arbitrary group access.

---

## Instagram Setup

**Only Option: OpenCLI (Desktop)**

**Prerequisites:**
- Chrome + OpenCLI extension
- Logged into instagram.com in Chrome

**Usage:**
```bash
opencli instagram search "username" -f yaml
opencli instagram user "username" --limit 12 -f yaml
```

> ⚠️ **Search = user search only**, not full-text post search.

---

## LinkedIn Setup

### Option A: linkedin-mcp (MCP Server)

**Setup:**
```bash
mcporter config add linkedin https://mcp.linkedin.scraper/mcp
```

**Usage:**
```bash
mcporter call 'linkedin.search_people(query: "query", limit: 10)'
mcporter call 'linkedin.get_profile(profile_url: "https://linkedin.com/in/username")'
```

### Option B: Jina Reader (Public pages only, no login)

```bash
curl -s "https://r.jina.ai/https://linkedin.com/in/username"
```

---

## 小宇宙 / Xiaoyuzhou Setup

**Setup (requires Whisper API key):**
```bash
mcporter config add xiaoyuzhou https://mcp.xiaoyuzhou/mcp
# Add API key to ~/.agent-reach/config.yaml or env
```

**Usage:**
```bash
mcporter call 'xiaoyuzhou.search_podcasts(keyword: "query", limit: 10)'
mcporter call 'xiaoyuzhou.get_episode(episode_id: "ID")'
```

---

## 雪球 / Xueqiu Setup

**Setup (requires cookie):**
```bash
mcporter config add xueqiu https://mcp.xueqiu/mcp
# Add cookie to config
```

**Usage:**
```bash
mcporter call 'xueqiu.get_quote(symbol: "SH600000")'
mcporter call 'xueqiu.search_stocks(keyword: "query", limit: 10)'
```

---

## Exa Semantic Search Setup

**Install mcporter:**
```bash
npm install -g mcporter
```

**Add Exa MCP:**
```bash
mcporter config add exa https://mcp.exa.ai/mcp
```

**Verify:**
```bash
mcporter call 'exa.web_search_exa(query: "test", numResults: 3)'
```

> Free tier: generous daily limits, no API key needed.

---

## Bilibili Setup (Optional Enhancement)

**For full features (beyond search API):**
```bash
pipx install bilibili-cli
# Or via pipx: pipx install git+https://github.com/public-clis/bilibili-cli.git
```

**Verify:**
```bash
bili search "test" --type video -n 1
```

---

## Environment-Specific Notes

### Local Desktop (Windows/Mac/Linux)
- OpenCLI works best — reuses YOUR browser login
- No proxy needed
- All platforms accessible via OpenCLI + CLI tools

### Remote Server / VPS / Docker
- OpenCLI NOT available (no browser)
- Use MCP servers (xiaohongshu-mcp, linkedin-mcp, xiaoyuzhou-mcp, xueqiu-mcp)
- CLI tools with cookies: twitter-cli, rdt-cli
- **Proxy REQUIRED** for China-blocked platforms (Twitter, Reddit, Facebook, Instagram, YouTube, 小红书)
- Proxy cost: ~$1/month for residential proxy

### CI/CD / GitHub Actions
- Use MCP servers or CLI tools with pre-configured cookies
- Store cookies in GitHub Secrets
- Use `--safe` mode for install to avoid system modifications

---

## Troubleshooting

### "Command not found" after install
```bash
# Reload shell or add to PATH
source ~/.bashrc  # or ~/.zshrc
# pipx ensures ~/.local/bin is in PATH
```

### OpenCLI "AUTH_REQUIRED" / "Not logged in"
1. Open Chrome
2. Go to platform (twitter.com, xiaohongshu.com, etc.)
3. Login manually
4. Refresh/retray command

### Rate limited / 429 / Captcha
- Space requests 2-3 seconds
- Use burner accounts
- Reduce concurrent requests
- For 小红书: xsec_token expires fast, re-search before each read

### mcporter timeout (120s default)
```bash
# Increase timeout for first-run browser downloads
mcporter call 'xiaohongshu.check_login_status()' --timeout 300000
```

### Windows: yt-dlp JS runtime error
```powershell
$cfg = 'C:\Users\pc\AppData\Roaming\yt-dlp\config'
New-Item -ItemType Directory -Force -Path (Split-Path $cfg) | Out-Null
if (-not (Test-Path $cfg) -or -not (Select-String -Path $cfg -Pattern '--js-runtimes' -Quiet)) {
  Add-Content -Path $cfg -Value '--js-runtimes node'
}
```

---

## Security Best Practices

1. **Use burner accounts** for all cookie-based platforms (Twitter, Reddit, FB, IG, 小红书, 雪球)
2. **Never commit cookies/tokens** to git — use `.env` or config.yaml (gitignored)
3. **Rotate cookies periodically** — platforms invalidate old sessions
4. **Monitor for ban signals** — 403, 429, "login required" on valid cookies
5. **Respect robots.txt / ToS** — this is for research, not mass scraping