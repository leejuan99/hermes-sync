---
name: hermes-messaging-gateway
description: "Use when setting up or fixing Hermes chat gateway."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, gateway, whatsapp, telegram, messaging, troubleshooting]
---

# Hermes Messaging Gateway

Connect and debug Hermes gateway chat platforms from the desktop app.

## Setup procedure

1. Run the platform wizard first, then the gateway:
   `hermes gateway setup` (pick platform) or `hermes whatsapp` for WhatsApp QR pairing.
2. Scan the QR via WhatsApp > Settings > Linked Devices > Link a Device.
3. Wait for `Pairing complete. Credentials saved`, then start `hermes gateway run` and leave it running.
4. Test by messaging the bot number from a second phone; expect an agent reply.
5. For always-on, use `hermes gateway install` then `hermes gateway start`.

## Verify state before guessing

- Check `gateway_state.json` (`platforms.whatsapp.state`) for `connected` vs error before touching config.
- Check `whatsapp/bridge.log` for `Bridge ready (status: connected)` and per-message `event` lines.
- Telegram `polling conflict` and `API_SERVER_KEY required` errors do not block WhatsApp; ignore them when only WhatsApp matters.
- Never run Linux panel commands (aaPanel paths) inside Windows PowerShell; they always fail with CommandNotFound.
- One active gateway per WhatsApp session: check for an already-running `gateway run`
  process before starting another; duplicates cause Telegram polling conflicts and
  WhatsApp session fights.
- Start long-lived gateway processes silent (no broad `error` notify patterns) and kill
  stale watchers; otherwise notification spam drowns real signals.

## VPS migration (24/7 bot)

- Full procedure: `references/vps-migration.md` — version match, secret transfer without
  displaying values, session copy to skip re-pairing, source-first cutover order,
  service install, skills/memory/MCP port.

## WhatsApp allowlist (no-reply root cause)

- An empty `WHATSAPP_ALLOWED_USERS` denies everyone by design; `*` opens the bot explicitly.
- Diagnose no-reply with bridge.log `ignored / allowlist_mismatch` plus sender in LID form (`NNNN@lid`).
- Resolve the sender LID to its phone via session file `lid-mapping-<LID>_reverse.json`, then add phone AND LID to `WHATSAPP_ALLOWED_USERS` (comma-separated in `.env`).
- WhatsApp increasingly addresses senders by LID, so an allowlist holding only the bot's own phone number silently drops real users; always include the actual sender identities.
- Restart the gateway after changing the allowlist; the bridge reads it once at startup.

## Desktop terminal assist

- When the user says the terminal shows nothing, force visibility with `terminal-deck` layout, then inspect with `read_terminal` (page with start_line/count for scrollback) instead of asking what they see.
- When the shell shows a continuation prompt (`>>` in PowerShell), tell them to cancel with Ctrl+C and re-enter the command cleanly.
- Answer "what do I type here" from the actual visible prompt (e.g. allowlist phone prompt takes comma-separated international numbers), not from generic docs.

## Telegram platform setup and marketing automation

1. Install Telegram messaging skill: `hermes skills install clawhub/telegram-messaging --yes`
2. Enable the plugin: `hermes config set plugins.enabled '["telegram-business"]'` (adjust if skill name differs)
3. Restart gateway: `hermes gateway restart`
4. Set Telegram bot token: `hermes config set telegram.token <token>`
5. Set webhook URL: `hermes config set telegram.webhook_url https://<domain>/webhooks/telegram`
6. Verify bot responds: send a message to the bot and check logs with `hermes logs | grep -i telegram`

## Telegram Platform Setup and Marketing Automation

1. Install Telegram messaging skill: `hermes skills install clawhub/telegram-messaging --yes`
2. Enable the plugin: `hermes config set plugins.enabled '["telegram-business"]'` (adjust if skill name differs)
3. Restart gateway: `hermes gateway restart`
4. Set Telegram bot token: `hermes config set telegram.token <token>`
5. Set webhook URL: `hermes config set telegram.webhook_url https://<domain>/webhooks/telegram`
6. Verify bot responds: send a message to the bot and check logs with `hermes logs | grep -i telegram`

## Telegram Polling Conflict Resolution

When getting `Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`:

```bash
# 1. Stop gateway completely
systemctl --user stop hermes-gateway
pkill -9 -f "hermes.*gateway"
sleep 5

# 2. Delete webhook & drop pending updates via Telegram API
BOT_TOKEN="<your_bot_token>"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"

# 3. Wait for Telegram to expire old session (5-10 minutes)
sleep 300

# 4. Start gateway
systemctl --user start hermes-gateway

# 5. Verify
journalctl -u hermes-gateway -n 30 --no-pager
```

**Pitfall:** Telegram long-polling connections persist server-side. Even after gateway restart, the old `getUpdates` connection remains active for ~5-10 minutes. `deleteWebhook?drop_pending_updates=true` forces immediate cleanup. Do NOT restart gateway repeatedly during this window — it creates more conflicts.

**Pitfall:** `api_server` requires `API_SERVER_KEY` in `.env` or config. Disable it (`enabled: false`) if not using OpenAI-compatible proxy.

**Pitfall:** WhatsApp adapter auto-enables if `WHATSAPP_ENABLED` not explicitly set to `false` in `.env`. Always set `WHATSAPP_ENABLED=false` unless actively pairing.

## Gateway Health Check
```bash
# Check service status
systemctl --user status hermes-gateway

# Check logs for platform connections
journalctl -u hermes-gateway -f

# Key success indicators:
# ✓ telegram connected
# ✓ webhook connected
# Gateway running with 1 platform(s)
# Telegram menu: 60 commands registered
```

## Marketing Automation Bots (Cron Jobs)

- Create wrapper scripts in `~/.hermes/scripts` that SSH to VPS and run bot scripts.
- Example wrapper for keyword-research:
  ```bash
  #!/usr/bin/env bash
  ssh -p 2222 -i "~/ .ssh/vps_key" root@<VPS_IP> "/root/.hermes/scripts/keyword-research-bot.sh"
  ```
- Make wrapper executable: `chmod +x ~/.hermes/scripts/wrapper-*.sh`
- Create cron jobs: `hermes cron create --name keyword-research --script wrapper-keyword-research.sh --no-agent "*/10 * * * *"` (repeat for other bots with appropriate schedules).
- Test a job immediately: `hermes cron run <job_id>`
- Verify logs and kanban board updates.

## Pitfalls

- Ensure SSH key is authorized on VPS (`~/.ssh/authorized_keys`) and that the VPS SSH port (2222) is accessible.
- When creating bot scripts on VPS, use proper variable quoting to avoid early expansion.
- Cron jobs run in `--no-agent` mode; output is delivered directly; check logs for success/failure.
- If a bot script fails, inspect its log in `~/.hermes/logs` and fix the script before re-running.
- Keep webhook secret in sync between Hermes config and Sejoli plugin panel.

