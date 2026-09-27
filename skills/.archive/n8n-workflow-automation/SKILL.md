---
name: n8n-workflow-automation
description: Class-level skill for building, deploying, and maintaining n8n workflows on VPS for automated content syndication, data pipelines, and scheduled tasks. Covers authenticated feed fetching, CLI tool integration, deduplication, error handling, and VPS deployment patterns.
version: 1.0.0
author: hermes-agent
tags:
  - n8n
  - workflow-automation
  - content-syndication
  - vps
  - docker
  - rss
  - api-integration
---

# n8n Workflow Automation Skill

## Overview

This skill covers the end-to-end pattern for building reliable n8n workflows on a self-hosted VPS (Docker) for scheduled automation tasks — particularly content syndication (RSS → platform posting), data pipelines, and recurring jobs.

## When to Use

- Scheduled fetching of authenticated feeds (RSS, API, web scraping with cookies)
- Transforming and filtering data (XML/JSON parsing, field mapping)
- Posting to external platforms via CLI tools or APIs (Gumroad, WordPress, social media)
- Deduplication across runs (static data, file, or DB)
- Error handling, logging, and monitoring
- Deploying on VPS with Docker (GreenCloud, aaPanel, custom)

## Core Workflow Pattern

```
Cron Trigger (schedule)
    ↓
HTTP Request (with auth headers/cookies)
    ↓
Parse (XML → JSON, or direct JSON)
    ↓
SplitInBatches (loop items)
    ↓
IF / Filter (validate, dedupe, conditionals)
    ↓
Execute Command / HTTP Request (post to target)
    ↓
IF (check error output)
    ├── Success → Log / Notify / Continue loop
    └── Error   → Log / Notify / Continue loop
    ↓
Loop back to SplitInBatches
```

## Key n8n Nodes Reference

| Node | Purpose | Key Config |
|------|---------|------------|
| **Cron** | Schedule (cron expression, timezone) | `0 8 * * *`, `Asia/Jakarta` |
| **HTTP Request** | Fetch feed with custom headers | Header Auth credential for cookies |
| **XML** | Parse RSS/Atom to JSON | `fieldToSplit: "rss.channel.item"` |
| **SplitInBatches** | Loop over array items | `batchSize: 1`, `reset: true` |
| **IF** | Filter/validate/route | Conditions on fields |
| **Execute Command** | Run CLI tool (gumroad-cli, wp-cli, etc.) | `command: "gumroad"`, `arguments: "products create ..."` |
| **Set** | Build log/notification payload | Expression syntax `{{$json.field}}` |
| **Function** | Custom JS logic (dedupe, transform) | Access `$getWorkflowStaticData()` |

## Authentication Patterns

### Cookie-Based (RSS behind login)
1. Create **HTTP Header Auth** credential
2. Header: `Cookie: name=value; name2=value2`
3. Reference in HTTP Request: `credentials: httpHeaderAuth`

### Token-Based (API)
1. Create **Generic Credential** or service-specific (GitHub, GitLab, etc.)
2. Use in HTTP Request Authorization header

### CLI Tools (gumroad-cli, wp-cli)
1. Install binary on VPS host (not in n8n container)
2. Auth once manually: `gumroad auth login --web`
3. Token stored in `~/.config/gumroad/` (persists across container restarts)
4. Execute Command node runs on host via Docker socket or SSH — **prefer host binary path**

## Deduplication Strategies

| Method | Persistence | Complexity | Use Case |
|--------|-------------|------------|----------|
| Workflow Static Data (`$getWorkflowStaticData('global')`) | In-memory (lost on n8n restart) | Low | Low volume, non-critical |
| File (JSON/CSV on host volume) | Survives restart | Medium | Medium volume, simple |
| SQLite / PostgreSQL | Survives restart, queryable | Higher | High volume, need querying |
| Redis | Fast, TTL support | Medium | High volume, distributed |

**Recommendation**: Start with static data → migrate to file/DB when needed.

## VPS Deployment Checklist

- [ ] n8n running in Docker (port 5678)
- [ ] Reverse proxy (aaPanel/nginx) → SSL, domain
- [ ] CLI tools installed on **host** (not container): `gumroad`, `wp`, `curl`, `jq`
- [ ] Docker volume for n8n data: `-v n8n_data:/home/node/.n8n`
- [ ] Timezone set: `TZ=Asia/Jakarta` in docker-compose
- [ ] Firewall: GreenCloud panel allow port 22 (SSH), 5678 (n8n if direct), 443/80 (proxy)
- [ ] Backup: cron job to dump n8n workflows + credentials (encrypted)

## Common Pitfalls & Fixes

| Pitfall | Fix |
|---------|-----|
| httpOnly cookies can't be set via browser JS | Use Playwright/Node script OR HTTP Header Auth in n8n (header passes raw cookie) |
| Execute Command runs in container, not host | Install CLI on host; use absolute path `/usr/local/bin/gumroad`; or mount Docker socket (security risk) |
| Workflow static data resets on n8n restart | Migrate to file-based dedupe: `Function` node reads/writes JSON on mounted volume |
| Cron timezone wrong | Set `TZ` env in docker-compose AND cron node timezone field |
| Cookie expires (14-30 days) | Add "refresh login" sub-workflow: POST to wp-login.php → extract new cookie → update credential via n8n API |
| Gumroad CLI needs interactive auth | Use `gumroad auth login --web` once manually; token persists. For CI: `GUMROAD_ACCESS_TOKEN` env var |
| Large RSS feeds timeout | Increase HTTP Request timeout (30s+); add pagination handling |

## Gumroad CLI Integration Details

```bash
# Install on VPS host
curl -fsSL https://gumroad.com/install-cli.sh | bash

# Auth (one-time, interactive)
gumroad auth login --web
# Opens browser → approve → token saved to ~/.config/gumroad/seller_token

# Create product (used in Execute Command node)
gumroad products create \
  --name "Product Title" \
  --description "Description here" \
  --url "https://download.link" \
  \
  --json
```

**Execute Command node config:**
```json
{
  "command": "gumroad",
  "arguments": "products create --name \"{{$json.title}}\" --description \"{{$json.description}}\" --url \"{{$json.link}}\" --json",
  "options": { "cwd": "/root" }
}
```

## Error Handling Pattern

```
Execute Command
    ↓
IF (stderr is not empty)
    ├── True  → Set (error log) → (optional) Notify Telegram/Email
    └── False → Set (success log) → (optional) Notify
    ↓
Continue loop (connect both branches back to SplitInBatches)
```

## References

- `references/gumroad-cli-cheatsheet.md` — Common commands, auth flows, JSON output parsing
- `references/rss-feed-patterns.md` — RSS/Atom field mapping, common variations
- `references/n8n-expressions-cheatsheet.md` — Expression syntax for data transformation
- `templates/wsodownloads-to-gumroad.json` — Starter workflow for WSO Downloads → Gumroad
- `scripts/refresh-wso-cookie.js` — Playwright script to re-login and extract fresh cookies