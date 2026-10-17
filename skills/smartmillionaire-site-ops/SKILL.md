---
name: smartmillionaire-site-ops
description: Use when editing smartmillionaire.co.id via MCP or VPS.
version: 1.0.0
tags: [wordpress, novamira, smartmillionaire]
---

# Smart Millionaire site ops

## Site map (all hosted on VPS alias `vps-hermes`: root@194.127.192.52:2222, key ~/.ssh/vps_key)
- Main site: `/www/wwwroot/smartmillionaire.co.id` (DB prefix `wpz6_`, front page ID **2**, user `yudira` ID 83)
- Member site (Sejoli): `/www/wwwroot/member.smartmillionaire.co.id` (user `leejuan`)
- wp-cli at `/usr/local/bin/wp` (use `--allow-root`)
- Site behind Cloudflare — verify live pages with a cache-buster query param (e.g. `?smmverify=123`)

## Homepage internals
- Homepage = **hand-coded HTML in post_content of page ID 2** (rendered via plugin `sm-homepage-enhancer`). It is NOT in `_elementor_data` — that meta is an 837KB leftover from an old Elementor build; ignore it.
- Edit flow: `wp post get 2 --field=content > /tmp/dump.html` → patch with python3 (assert each target string found exactly once before replacing) → write back via `wp eval-file` running `wp_update_post` → verify live with cache-buster + grep old & new markers.
- Backup before edit: `/tmp/smm-home-backup-*.html` (2026-10-17 backup = pre-"Strategic Business Partner" repositioning version).

## MCP (Novamira) connection
- Config: `%LOCALAPPDATA%/hermes/mcp_servers.yaml` — `novamira-smartmillionaire`, `novamira-member`, `novamira-leejuan-com` are stdio servers via `npx @automattic/mcp-wordpress-remote` with WP application-password env vars.
- Symptom of dead creds: MCP source missing from tool_search after a session restart; curl to `/wp-json/wp/v2/users/me` returns 401 `rest_not_logged_in` (endpoint itself still responds).
- Rotate: `wp user application-password create <user> <label> --porcelain --allow-root` on the VPS → update `mcp_servers.yaml` → verify with POST `initialize` (expect HTTP 200 + `serverInfo`) → user restarts chat session so Hermes reloads MCP tools.