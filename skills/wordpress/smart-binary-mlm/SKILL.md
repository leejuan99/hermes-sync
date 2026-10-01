---
name: smart-binary-mlm
description: "Use when working on the Smart Binary MLM plugin."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [mlm, binary, wordpress, sejoli, commissions]
metadata:
  hermes:
    tags: [mlm, binary, wordpress, sejoli, commissions]
    related_skills: [wordpress-mcp-integration, subagent-fanout, novamira-mcp-troubleshooting]
---

# Smart Binary MLM plugin (member.smartmillionaire.co.id)

## When to Use

Any task touching the smart-binary MLM plugin or the member site's MLM/commission/admin code: bug fixing, bonus/commission configuration, payout logic, admin UI changes, MCP access, audits.

Custom WordPress binary-plan MLM plugin "smart-binary" on the PRODUCTION membership site member.smartmillionaire.co.id — real members and real IDR commissions/payouts (~3,400 members).

## Site & access

- Separate WP install from smartmillionaire.co.id (own DB, own credentials). Admin: leejuan (ID 1). DB prefix `wplo_`. Plugin dir: `/www/wwwroot/member.smartmillionaire.co.id/wp-content/plugins/smart-binary`.
- VPS: `ssh -i ~/.ssh/vps_key -p 2222 -o StrictHostKeyChecking=no root@194.127.192.52`. WP-CLI: `cd /www/wwwroot/member.smartmillionaire.co.id && wp ... --allow-root`.
- MCP: server `novamira-member` (npx @automattic/mcp-wordpress-remote, WP_API_URL=https://member.smartmillionaire.co.id/wp-json/mcp/novamira, user leejuan, app password generated via WP-CLI `wp user application-password create`). Tools load after `/reload-mcp` or a new session.
- BEFORE any production edit: `tar czf /www/wwwroot/backups/smart-binary-<tag>-$(date +%Y%m%d%H%M).tar.gz smart-binary` from the plugins dir.

## Architecture map

- Point-based commission, NO BV (v1.0.0). Packages Starter/Pro/Elite. Tables `{prefix}sb_*` (~29).
- `includes/core/`: sb-member (placement, activation, triple-bundle), sb-tree (binary legs, BV propagation, foundation leg), sb-period, sb-point-system (leg points per YYYY-MM period), sb-wallet, sb-payout, sb-currency, sb-rank, sb-package, sb-subscription.
- `includes/bonuses/`: one class per bonus type + engine + base (pairing, sponsor, level, matching, pool, teampool, royalty, faststart, ROB, leadership, shared milestone, rank achievement, subscription shield, level pairing).
- `includes/integrations/`: **Sejoli = the LIVE store path**; WooCommerce & FluentCart = on hold.
- `includes/notifications/`: email/telegram/whatsapp senders, templates, logs.
- `includes/class-sb-rest.php` (~1,300 lines): Vue admin SPA API under /mlm/v1, all routes gated by `current_user_can('manage_options')`.
- `admin/`: PHP page partials + Vue app.js (~1,500 lines). `public/`: member dashboards, shortcodes, webinar room.

## User's standing decisions (do not contradict)

- NO BV — points are the pairing unit, money is integer Rupiah. Never reintroduce BV math.
- WooCommerce & FluentCart integrations ON HOLD (unused by the business): don't fix, don't refactor, don't "improve". Sejoli is what pays.
- Simplify the plan toward 4 bonus types: Sponsor + Pairing + Matching + Milestone. Do not add bonus types without the user asking.
- Admin panel is considered ugly/messy by the user: menu must be reorganized by category (bonus settings are scattered across Settings/Bonus pages), notifications must be deletable, and any redesign must introduce ZERO errors (php -l / node --check everything).
- Production fix protocol: backup → fresh scp → patch → scp back → php -l → smoke test (site HTTP 200 + `wp eval 'echo "boot-ok";'`). Demo/seed endpoints must never touch production data.

## Audit / fix workflow

Fan out parallel subagents by module with exclusive file ownership (see the `subagent-fanout` skill). scp the plugin to local scratch, flatten the nested dir, then dispatch. Bug inventory with file:line in `references/bug-inventory.md`.
