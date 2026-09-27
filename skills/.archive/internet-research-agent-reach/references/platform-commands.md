# Platform Commands Reference

Complete command reference per platform and backend for Agent Reach.

## Zero-Config Platforms (No Setup Required)

### Web Pages — Jina Reader
```bash
# Read any public web page
curl -s "https://r.jina.ai/https://example.com/article"

# With custom timeout
curl -s --max-time 30 "https://r.jina.ai/URL"
```

### YouTube — yt-dlp
```bash
# Get subtitles (auto-generated + manual)
yt-dlp --write-sub --write-auto-sub --skip-download -o "/tmp/%(id)s" "https://youtube.com/watch?v=VIDEO_ID"

# Get video info only
yt-dlp --dump-json --no-download "URL"

# Search YouTube
yt-dlp "ytsearch10:query" --dump-json --no-download
```

### GitHub — gh CLI
```bash
# Repo info
gh repo view owner/repo

# Search repos
gh search repos "query" --sort stars --limit 10 --json name,description,stargazerCount,url

# Search code
gh search code "query" --limit 10

# List issues
gh issue list --repo owner/repo --limit 10 --json number,title,state,url

# Read file from repo
gh api repos/owner/repo/contents/path/to/file --jq .content | base64 -d
```

### Bilibili — bili-cli (Preferred) / OpenCLI
```bash
# Search videos (no login)
bili search "query" --type video -n 10

# Search users
bili search "query" --type user -n 10

# Video detail
bili video BVxxxxxx

# User videos
bili user-space UID --page 1 --pagesize 20

# Hot ranking
bili hot -n 20

# Subtitles (OpenCLI - needs Chrome login)
opencli bilibili subtitle BVxxxxxx
```

### V2EX — Public API
```bash
# Hot topics
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"

# Node topics (python, tech, jobs, qna, programmers, etc.)
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" -H "User-Agent: agent-reach/1.0"

# Topic detail + replies
curl -s "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID" -H "User-Agent: agent-reach/1.0"
curl -s "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" -H "User-Agent: agent-reach/1.0"

# User info
curl -s "https://www.v2ex.com/api/members/show.json?username=USERNAME" -H "User-Agent: agent-reach/1.0"
```

### RSS/Atom — feedparser (Python)
```python
import feedparser
feed = feedparser.parse("https://example.com/feed.xml")
for entry in feed.entries[:10]:
    print(entry.title, entry.link, entry.published)
```

### Exa Semantic Search — mcporter + Exa MCP
```bash
# Install once
npm install -g mcporter
mcporter config add exa https://mcp.exa.ai/mcp

# Search
mcporter call 'exa.web_search_exa(query: "your query", numResults: 10)'

# Search with options
mcporter call 'exa.web_search_exa(query: "query", numResults: 10, type: "neural", useAutoprompt: true)'
```

---

## Login-Backed Platforms (Require Setup)

### Twitter/X

#### Backend A: twitter-cli (Preferred for search)
```bash
# Install
pipx install twitter-cli
# Set cookies: export TWITTER_AUTH_TOKEN=... TWITTER_CT0=...

# Search tweets
twitter search "query" -n 20

# User timeline
twitter user-posts @username -n 20

# Single tweet + replies
twitter tweet "https://x.com/user/status/123456789"

# User profile
twitter user @username

# Home feed
twitter feed -n 20
```

#### Backend B: OpenCLI (Desktop, browser login)
```bash
# Install OpenCLI Chrome extension + pipx install opencli

# Search
opencli twitter search "query" -f yaml

# User posts
opencli twitter user-posts @username -f yaml

# Tweet detail
opencli twitter tweet "URL" -f yaml
```

> **Retry chain if search fails:**
> 1. Retry once
> 2. `pipx upgrade twitter-cli && twitter search "query" -n 10`
> 3. Fallback to OpenCLI: `opencli twitter search "query" -f yaml`
> 4. Use stable commands only: `twitter feed`, `twitter user-posts`

### Reddit

#### Backend A: OpenCLI (Desktop, browser login)
```bash
# Search posts
opencli reddit search "query" -f yaml

# Read post + comments
opencli reddit read POST_ID -f yaml

# Browse subreddit
opencli reddit subreddit LocalLLaMA -f yaml

# Hot/Popular
opencli reddit hot -f yaml
opencli reddit popular -f yaml

# Subreddit info
opencli reddit subreddit-info LocalLLaMA -f yaml
```

#### Backend B: rdt-cli (Legacy/Server)
```bash
# Install from GitHub (PyPI version outdated)
pipx install 'git+https://github.com/public-clis/rdt-cli.git'
rdt login  # Interactive, or manually write cookie

# Search
rdt search "query" --limit 10

# Read post
rdt read POST_ID

# Browse subreddit
rdt sub python --limit 20
rdt popular --limit 10
rdt all --limit 10
```

> **Note:** No zero-config path. Anonymous `.json` endpoints return 403. Official API requires approval (rarely granted for personal projects).

### 小红书 / XiaoHongShu

#### Backend A: OpenCLI (Desktop, browser login) — Preferred
```bash
# Search notes
opencli xiaohongshu search "query" -f yaml

# Read note (MUST use full URL from search result with xsec_token)
opencli xiaohongshu note "https://www.xiaohongshu.com/explore/NOTE_ID?xsec_token=TOKEN" -f yaml

# Comments
opencli xiaohongshu comments NOTE_ID -f yaml

# Feed
opencli xiaohongshu feed -f yaml

# User notes
opencli xiaohongshu user USER_ID -f yaml
```

#### Backend B: xiaohongshu-mcp (Server, QR login)
```bash
# Check login
mcporter call 'xiaohongshu.check_login_status()' --timeout 120000

# Get QR code
mcporter call 'xiaohongshu.get_login_qrcode()' --timeout 120000

# Search
mcporter call 'xiaohongshu.search_feeds(keyword: "query")' --timeout 120000

# Note detail
mcporter call 'xiaohongshu.get_feed_detail(feed_id: "ID", xsec_token: "TOKEN")' --timeout 120000
```

#### Backend C: xhs-cli (Legacy, unstable)
```bash
# Author moved to OpenCLI (2026-03). Unstable: user/user-posts/favorites may 406.
xhs search "query"
xhs read "NOTE_URL_FROM_SEARCH"  # Must use search result URL, not bare ID
xhs comments "NOTE_URL"
xhs hot
xhs feed
```

> **Critical:** **xsec_token is mandatory** — cannot use bare note_id. Always get full URL from search/feed first.
> **Rate limit:** 2-3s between requests to avoid captcha.

### Facebook

#### Backend: OpenCLI (Desktop, browser login)
```bash
# Search users/pages/posts
opencli facebook search "query" -f yaml

# Profile/page info
opencli facebook profile zuck -f yaml

# Your news feed
opencli facebook feed --limit 10 -f yaml

# Your visible groups (list + recent activity)
opencli facebook groups --limit 20 -f yaml
```

> **Limitation:** Only reads groups **visible to your account**. No API for arbitrary group posts/comments.

### Instagram

#### Backend: OpenCLI (Desktop, browser login)
```bash
# Search users (NOT full-text post search)
opencli instagram search "query" -f yaml

# User profile
opencli instagram profile username -f yaml

# User recent posts
opencli instagram user username --limit 12 -f yaml

# Explore
opencli instagram explore --limit 20 -f yaml

# Saved posts
opencli instagram saved --limit 20 -f yaml
```

> **Note:** `instagram search` = user search only. To read posts, need username first.

### LinkedIn

#### Backend: linkedin-mcp (MCP Server)
```bash
# Setup
mcporter config add linkedin https://mcp.linkedin.scraper/mcp

# Search people
mcporter call 'linkedin.search_people(query: "query", limit: 10)'

# Profile detail
mcporter call 'linkedin.get_profile(profile_url: "https://linkedin.com/in/username")'

# Company page
mcporter call 'linkedin.get_company(company_url: "https://linkedin.com/company/name")'

# Jobs
mcporter call 'linkedin.search_jobs(keywords: "query", location: "city", limit: 10)'
```

#### Fallback: Jina Reader (public pages only)
```bash
curl -s "https://r.jina.ai/https://linkedin.com/in/username"
```

### 小宇宙 / Xiaoyuzhou Podcast

#### Backend: xiaoyuzhou-mcp (Whisper transcription)
```bash
# Setup: needs Whisper API key
mcporter config add xiaoyuzhou https://mcp.xiaoyuzhou/mcp

# Search podcasts
mcporter call 'xiaoyuzhou.search_podcasts(keyword: "query", limit: 10)'

# Get episode + transcript
mcporter call 'xiaoyuzhou.get_episode(episode_id: "ID")'
```

### 雪球 / Xueqiu (Stocks)

#### Backend: xueqiu-mcp
```bash
# Setup: needs cookie
mcporter config add xueqiu https://mcp.xueqiu/mcp

# Stock quote
mcporter call 'xueqiu.get_quote(symbol: "SH600000")'

# Search stocks
mcporter call 'xueqiu.search_stocks(keyword: "query", limit: 10)'

# Hot posts
mcporter call 'xueqiu.get_hot_posts(limit: 20)'
```

---

## Platform Selection Guide

| Research Goal | Primary Platforms | Commands |
|---------------|-------------------|----------|
| **General web facts** | Exa + Jina Reader | `mcporter call exa.web_search_exa`, `curl r.jina.ai/URL` |
| **Chinese social sentiment** | 小红书 + B站 + V2EX | `opencli xiaohongshu search`, `bili search`, `curl v2ex api` |
| **Tech discussions** | GitHub + Reddit + Twitter + V2EX | `gh search`, `opencli reddit search`, `twitter search` |
| **Video content** | YouTube + B站 + 小宇宙 | `yt-dlp subs`, `bili search`, `xiaoyuzhou get_episode` |
| **Finance/stocks** | 雪球 + Twitter | `xueqiu get_quote`, `twitter search $SYMBOL` |
| **Jobs/recruiting** | LinkedIn + V2EX jobs | `linkedin search_jobs`, `curl v2ex node=jobs` |
| **Academic** | arXiv + GitHub + web | (use arxiv skill + gh + Exa) |