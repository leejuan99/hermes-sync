---
name: wordpress-mcp-fluentcrm
description: "Operate WordPress + Fluent CRM via Novamira MCP server from Hermes. Covers MCP setup, fetching/analyzing contacts, bulk operations, and fake email detection."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wordpress, mcp, novamira, fluent-crm, crm, email-validation]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [hermes-agent, autonomous-ai-agents]
---

# WordPress MCP + Fluent CRM Integration Skill

This skill covers the complete workflow for connecting Hermes to a WordPress site running Fluent CRM via the Novamira plugin's MCP server, fetching contacts, analyzing for fake/spam emails, and performing bulk operations.

## Quick Start

### 1. Prerequisites

- WordPress site with **Novamira plugin** installed and activated
- **Fluent CRM** plugin installed
- **Application Password** created for a WordPress user with Fluent CRM permissions
- Node.js + npx available

### 2. Add MCP Server to Hermes

```bash
hermes mcp add novamira-mysite \
  --command npx \
  --args '["-y", "@automattic/mcp-wordpress-remote@latest"]' \
  --env WP_API_URL=https://yoursite.com/wp-json/mcp/novamira,WP_API_USERNAME=youruser,WP_API_PASSWORD=apppassword
```

### 3. Test Connection

```bash
hermes mcp test novamira-mysite
```

Expected: `✓ Connected` with 3 tools discovered:
- `mcp-adapter-discover-abilities`
- `mcp-adapter-get-ability-info`
- `mcp-adapter-execute-ability`

### 4. Fetch All Contacts

```bash
python scripts/fetch-all-contacts.py \
  --output contacts.json \
  --wp-url https://yoursite.com/wp-json/mcp/novamira \
  --wp-user youruser \
  --wp-pass apppassword
```

### 5. Analyze for Fake Emails

```bash
python scripts/analyze-fake-emails.py \
  --input contacts.json \
  --output suspicious.json \
  --min-confidence HIGH
```

### 6. Review & Delete

```bash
# View HIGH confidence fakes
python scripts/analyze-fake-emails.py --input contacts.json --output suspicious.json --min-confidence HIGH

# Or review all
cat suspicious.json | jq '.[] | {id, email, first_name, _analysis}'
```

## Core Workflows

### Fetch & Analyze (One-Shot)

```bash
# Complete pipeline
hermes chat -q "
  Use Novamira MCP to fetch all Fluent CRM contacts,
  then run the fake email analyzer script,
  and report HIGH confidence fakes for deletion.
" --toolsets mcp,terminal
```

### Bulk Delete Confirmed Fakes

```python
# After reviewing suspicious.json, delete via MCP
for contact in confirmed_fakes:
    call_mcp("mcp-adapter-execute-ability", {
        "ability_name": "fluent-crm/delete-contact",
        "parameters": {"id": contact["id"], "delete_emails": true}
    })
```

### Fix Typo Domains

```python
# For MEDIUM confidence typo domains (gmal.com → gmail.com)
for contact in typo_contacts:
    fixed_email = contact['email'].replace('@gmal.com', '@gmail.com')
    call_mcp("mcp-adapter-execute-ability", {
        "ability_name": "fluent-crm/upsert-contact",
        "parameters": {"id": contact["id"], "email": fixed_email}
    })
```

## Key Files

| File | Purpose |
|------|---------|
| `scripts/fetch-all-contacts.py` | Fetch all contacts via MCP with pagination |
| `scripts/analyze-fake-emails.py` | Score contacts for fakeness (HIGH/MEDIUM/LOW/CLEAN) |
| `references/fake-email-patterns.md` | Complete detection rules & production results |
| `references/novamira-mcp-abilities.md` | All 21 Fluent CRM abilities + calling patterns |

## Fake Email Detection Rules (Summary)

| Pattern | Score | Confidence |
|---------|-------|------------|
| Disposable domain (mailinator, 10minutemail, etc) | +15 | HIGH |
| Email used as name | +15 | HIGH |
| 6+ consecutive consonants | +10 | HIGH |
| Keyboard pattern (qwerty, asdfgh, 123456) | +10 | HIGH |
| 5+ repeated chars (aaaaa) | +10 | HIGH |
| Gibberish first name | +10 | HIGH |
| Known fake from production data | +15 | HIGH |
| Typo domain (gmal.com, gamil.com, dmain.com) | +3 | MEDIUM |
| High entropy random string | +3 | MEDIUM |
| Long number sequence (5+ digits) | +3 | MEDIUM |
| Name/email mismatch | +2 | LOW |
| Fake keyword (test, fake, spam, temp) | +5 | MEDIUM |

**Positive signals reduce score:** Last activity (-2), legitimate source (-1), subscribed+active (-1), name prefix matches (-2), Indonesian corporate/edu domains (-3).

## Production Results (2,287 contacts)

| Category | Count | % | Action |
|----------|-------|---|--------|
| HIGH (delete) | ~15 | 0.7% | Immediate bulk delete |
| Typo domains (fix) | 138 | 6% | Review → fix or delete |
| MEDIUM (review) | 529 | 23% | Prioritize unsubscribed |
| LOW (monitor) | 146 | 6% | Track engagement |
| CLEAN | 1,460 | 64% | Keep |

## Common Pitfalls

1. **MCP connection timeout** — Increase `mcp_discovery_timeout` in Hermes config (`hermes config set mcp_discovery_timeout 10`)
2. **npx not in PATH** — Use full path: `C:\Program Files\nodejs\npx.cmd` on Windows
3. **Application password expired** — Regenerate in WordPress Users → Profile → Application Passwords
4. **Rate limiting** — Add 500ms delay between bulk operations
5. **Double-encoded JSON** — MCP response text field is double-encoded; parse twice
6. **Page size limit** — Max 100 per page for `list-contacts`; use 100 and paginate

## Related Skills

- `hermes-agent` — Core Hermes configuration & MCP management
- `autonomous-ai-agents/hermes-agent` — Spawning agents for parallel processing