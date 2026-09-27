---
name: internet-research-agent-reach
description: "Use Agent Reach to give AI agents internet capabilities across 15 platforms (Twitter/X, Reddit, Facebook, Instagram, YouTube, GitHub, Bilibili, XiaoHongShu, LinkedIn, V2EX, Xueqiu, RSS, web search, web pages, podcasts). Multi-backend routing with zero-config channels. Run `agent-reach doctor --json` to see active backend per platform."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [internet, research, agent-reach, web-search, social-media, scraping, multi-platform]
    related_skills: [web-search, youtube-content, github-repo-management, arxiv, blogwatcher]
---

# Internet Research with Agent Reach

**Agent Reach** is a capability layer that gives AI agents "eyes" to read the internet across 15+ platforms. It handles platform selection, installation, health-checks, and routing — you don't need to know which CLI or API to use for each platform.

## When to Use

- User asks to "research X", "search the web for Y", "find what people say about Z"
- User shares any URL from supported platforms (Twitter, Reddit, YouTube, GitHub, Bilibili, 小红书, etc.)
- Need to fetch content from platforms that require login (Twitter, Reddit, FB, IG, 小红书, LinkedIn)
- Need semantic web search (Exa AI via MCP)
- Need to monitor RSS feeds or V2EX

**NOT for:** writing reports/analysis/translation (only FETCHES content); posting/commenting/liking (write operations); platforms with dedicated skills already installed.

## Installation

```bash
# One-liner for any AI agent (Claude Code, Cursor, Windsurf, OpenClaw, Codex)
# The agent will self-install everything
"Help me install Agent Reach: https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md"

# Or manual install
pip install agent-reach
agent-reach install --env=auto
```

## Quick Health Check

```bash
# See which backend serves each platform RIGHT NOW
agent-reach doctor --json

# Human-readable status
agent-reach doctor
```

## Zero-Config Channels (Work Immediately)

| Platform | Command | Notes |
|----------|---------|-------|
| **Web page** | `curl -s "https://r.jina.ai/URL"` | Any public URL |
| **YouTube** | `yt-dlp --write-sub --skip-download "URL"` | Subtitles + metadata |
| **GitHub** | `gh repo view owner/repo` | Public repos; `gh auth login` for private |
| **Bilibili** | `bili search "query" --type video -n 5` | No login needed |
| **V2EX** | `curl -s "https://www.v2ex.com/api/topics/hot.json"` | Public API |
| **RSS/Atom** | Python `feedparser` | Any feed URL |
| **Exa web search** | `mcporter call 'exa.web_search_exa(query: "...", numResults: 5)'` | Needs `mcporter` + Exa MCP setup |

## Login-Backed Platforms (Require Setup)

| Platform | Desktop (OpenCLI) | Server (MCP/CLI) | Setup |
|----------|-------------------|------------------|-------|
| **Twitter/X** | `opencli twitter search "query" -f yaml` | `twitter-cli` (needs cookie) | `pipx install twitter-cli` + cookie |
| **Reddit** | `opencli reddit search "query" -f yaml` | `rdt-cli` (needs cookie) | Browser login + OpenCLI ext |
| **小红书** | `opencli xiaohongshu search "query" -f yaml` | `xiaohongshu-mcp` (QR login) | Browser login + OpenCLI ext |
| **Facebook** | `opencli facebook search "query" -f yaml` | — | Browser login + OpenCLI ext |
| **Instagram** | `opencli instagram search "query" -f yaml` | — | Browser login + OpenCLI ext |
| **LinkedIn** | — | `linkedin-mcp` (MCP) | `mcporter config add linkedin ...` |
| **小宇宙** | — | `xiaoyuzhou-mcp` (Whisper) | Whisper API key |
| **雪球** | — | `xueqiu-mcp` | Cookie |

> **OpenCLI** = Chrome extension that reuses your browser login state. Install from Chrome Web Store, then `pipx install opencli`.

## Research Workflow Pattern

```python
# 1. Health check first
agent_reach_doctor = run("agent-reach doctor --json")

# 2. Pick platforms based on query type
# - General web: Exa search + Jina Reader
# - Chinese social: 小红书 + B站 + V2EX
# - Tech/discussion: GitHub + Reddit + Twitter + V2EX
# - Video: YouTube + B站 + 小宇宙
# - Finance: 雪球 + Twitter

# 3. Run searches in parallel (delegate_task batch)
# 4. Synthesize findings
```

## Common Pitfalls

1. **Assuming zero-config works for login platforms** — Twitter, Reddit, FB, IG, 小红书 NEED login. Always run `agent-reach doctor` first.
2. **Using yt-dlp for Bilibili** — BLOCKED by risk control (412). Use `bili-cli` or OpenCLI.
3. **Not respecting rate limits** — 小红书 xsec_token required; high frequency triggers captcha. Space requests 2-3s.
4. **Using main account for scraping** — Use **burner accounts** for cookie-based platforms. Risk of ban.
5. **Expecting Facebook Group post access** — NOT SUPPORTED. Only visible groups list + recent feed activity.
6. **Ignoring `active_backend`** — Platform routing changes. Always check `doctor --json` before choosing commands.

## Verification Checklist

- [ ] Ran `agent-reach doctor --json` before starting
- [ ] Selected correct backend per platform from `active_backend`
- [ ] Used zero-config channels where possible (Web, YouTube, GitHub, B站, V2EX, RSS)
- [ ] For login platforms: verified OpenCLI extension installed + browser logged in
- [ ] Respected rate limits (2-3s between requests)
- [ ] Used burner accounts for cookie-based auth
- [ ] Cited sources with platform + URL in final output

## One-Shot Recipes

### "Research [topic] across Chinese social media"
```bash
# 小红书
opencli xiaohongshu search "topic" -f yaml
# B站
bili search "topic" --type video -n 10
# V2EX
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=tech&page=1"
```

### "Research [topic] across English tech platforms"
```bash
# Exa semantic search
mcporter call 'exa.web_search_exa(query: "topic", numResults: 10)'
# GitHub
gh search repos "topic" --sort stars --limit 10
# Reddit
opencli reddit search "topic" -f yaml
# Twitter
twitter search "topic" -n 20
```

### "Get video transcript + summary"
```bash
# YouTube
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"
# B站 (via OpenCLI)
opencli bilibili subtitle BVxxx
```

## Reference Files

- `references/platform-commands.md` — Complete command reference per platform/backend
- `references/setup-guide.md` — Detailed setup for each login-backed platform
- `references/rate-limits.md` — Known rate limits and anti-patterns per platform