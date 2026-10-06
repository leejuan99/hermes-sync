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

- Check `gateway_state.json` (`platforms.telegram.state` / `platforms.whatsapp.state`) for `connected` vs error before touching config; `gateway_state.json` is the source of truth, not `hermes -p <name> cron status` under multiplex.
- Check `whatsapp/bridge.log` for `Bridge ready (status: connected)` and per-message `event` lines.
- Telegram `polling conflict` and `API_SERVER_KEY required` errors do not block WhatsApp; ignore them when only WhatsApp matters.
- Explicit `platforms.telegram.enabled: false` in `config.yaml` silently disables Telegram even when `TELEGRAM_BOT_TOKEN` is set in `.env` — the log says `Platform 'telegram' is explicitly disabled ... will NOT start its adapter`. Fix with `hermes config set platforms.telegram.enabled true` then `hermes gateway restart`.
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

## Multiple profiles on one gateway (multiplex)

A profile is a division: its own home under `profiles/<name>/` with its own memory, skills, sessions
and cron jobs. One gateway can serve all of them instead of one gateway per profile.

- Enable with `hermes config set gateway.multiplex_profiles true`, then restart the service.
  `gateway.multiplex_profile_allowlist` no longer exists (config v43+): a multiplexing gateway serves
  **every** profile under `profiles/`, so retire a profile by archiving or deleting it.
- **Verify with the log, never with the per-profile status line.** Under multiplex,
  `hermes -p <name> cron status` reports `✗ Gateway is not running — cron jobs will NOT fire` for
  every secondary profile. That is a **false negative** — the check looks for a gateway launched with
  that profile's home, and the multiplexed gateway launched as `default`. The jobs do fire. Confirm:

  ```bash
  grep 'tick .* profile(s) under multiplex' ~/.hermes/logs/gateway.log
  # → Cron scheduler will tick 2 profile(s) under multiplex: ['default', 'dm']
  ```

  If that line names the profile, the setup is correct — do not start a second gateway to "fix"
  the status line, or you get the polling conflict below.
- **One bot token, one profile.** Adapters take a scoped lock on their credential, so two profiles
  cannot share a bot token: the second silently fails to connect and the first starts seeing
  `Conflict: terminated by other getUpdates request`. Differential-diagnose by checking whether the
  platform variables are live (uncommented) in the profile's `.env`.
- **`hermes profile create X --clone` copies `.env` but not the `platforms:` config section.**
  Since platforms are usually enabled from `.env`, the clone silently claims the *same* bot as the
  original. Before turning on multiplex, back up and comment the platform variables out of the
  clone's `.env`, or give the clone its own bot.
- **A profile with no platform credentials cannot report anywhere.**
  `hermes -p <name> send -t telegram` fails with `Platform 'telegram' is not configured.`
  A division that must send its own reports needs its own bot: create one with @BotFather
  (`/newbot`) and put that token in the profile's `.env`. This is the intended shape, not a workaround.

## The bot answers with the wrong model

`config.yaml`'s `model.default` is only the default for *new* sessions. Three independent pins decide
what a live bot actually uses:

| Pin | Where | Rewritten by |
|---|---|---|
| Session model | `state.db` → `sessions.model` | every model pick |
| Session override | `sessions.json` → `model_override` | the chat `/model` command |
| Per-job pin | `cron/jobs.json` → `model_snapshot` | at job creation |

So a bot can keep answering on the old model after `hermes config set model.default ...`, and editing
`sessions.json` alone does nothing because `state.db` is what the gateway reads back.

The chat `/model` menu is also a trap: it lists Hermes' *built-in* providers, so a user selecting a
`*-free` entry can silently override a working setup with one that answers `HTTP 500` or
`400 Model is unavailable`. When a bot that was fine starts erroring, read `sessions.model` out of
`state.db` before touching any config — and never `grep -r` the Hermes home to find it, since its
multi-megabyte caches return model ids that only *look* like settings.

Full clear-and-restart recipe: `hermes-multimachine-sync` → `references/model-routing.md`.

## Gemini model/provider setup for Telegram bot

If you want to use Google Gemini models for your Telegram bot, follow these steps:

1. Set model and provider in `~/.hermes/config.yaml`:
   ```yaml
   model:
     default: gemini-3.5-flash   # or any available Gemini model
     provider: google
   ```
2. Ensure the Google/OpenAI‑compatible endpoint is correct:
   ```
   providers:
     google:
       base_url: https://generativelanguage.googleapis.com/v1beta/openai
       key_env: GEMINI_API_KEY
   ```
3. In `~/.hermes/.env`, uncomment and set:
   ```
   GEMINI_API_KEY=your_actual_gemini_key_here
   GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
   ```
4. Clear any existing session overrides that may force a different model:
   - Delete `~/.hermes/sessions/sessions.json` (or rename it) to let the gateway create a fresh session file.
   - Or, via SQLite: `sqlite3 ~/.hermes/state.db "UPDATE sessions SET model_override = NULL WHERE source = 'telegram';"`
   - Then set the correct model and model_config for Telegram sessions:
     ```
     sqlite3 ~/.hermes/state.db "UPDATE sessions SET model = 'gemini-3.5-flash', model_config = '{'gateway_runtime': {'provider': 'google', 'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai', 'api_mode': 'chat_completions', 'fallback_active': false}, 'model': 'gemini-3.5-flash', 'provider': 'google'}' WHERE source = 'telegram';"
     ```
5. Restart the gateway so the new configuration is loaded:
   ```
   systemctl --user restart hermes-gateway
   ```
   (This command requires user approval; run it when prompted.)
6. Verify the bot is using Gemini:
   - Send a test message to the Telegram bot.
   - Or run `hermes -z "test"` and check the response.
   - If you still see API key errors, double‑check that the `.env` file contains the correct key and that there are no leading/trailing spaces.

## Routing a bot to 9Router

To route any Telegram/WhatsApp bot through 9Router instead of OpenRouter/Command Code:

```bash
hermes config set model.provider 9router
hermes config set model.base_url https://9router.smartmillionaire.co.id/v1
hermes config set model.default 9router_combo_1
hermes config set model.key_env HERMES_CUSTOM_9ROUTER_API_KEY
# Telegram toggle is independent — env token is ignored when disabled:
hermes config set platforms.telegram.enabled true
hermes gateway restart
```
Verify: `curl -H "Authorization: Bearer $HERMES_CUSTOM_9ROUTER_API_KEY" https://9router.smartmillionaire.co.id/v1/models` lists `9router_combo_1`; `cat ~/.hermes/gateway_state.json` shows `platforms.telegram.state: "connected"` and `model.default: 9router_combo_1`. The session pin in `state.db` (`sessions.model`) and `sessions.json` (`model_override` from `/model`) overrides `config.yaml` for live chats — send `/new` in Telegram to start a fresh session on the new model. Discover other 9Router models with `curl -H "Authorization: Bearer $HERMES_CUSTOM_9ROUTER_API_KEY" https://9router.smartmillionaire.co.id/v1/models | jq .data[].id`.

## Marketing Automation Bots (Cron Jobs)

Create the job **on the host that runs the gateway**. A job created on the desktop machine dies with
that machine; an SSH wrapper that reaches the VPS from the desktop is strictly worse than creating
the same job on the VPS.

- Put wrapper scripts in the **owning profile's** scripts directory: `~/.hermes/scripts/` for
  `default`, `~/.hermes/profiles/<name>/scripts/` for any other profile. `hermes cron create --script`
  takes a bare filename and rejects absolute or home-relative paths.
- A wrapper is any file that prints the prompt on stdout — a tiny Python reader is enough:

  ```python
  with open('/root/.hermes/marketing/prompts/dm/01-trend-scout.txt', 'r', encoding='utf-8') as f:
      print(f.read())
  ```

  Generating wrappers with a here-doc loop *through SSH* mangles `$` expansion and produces
  wrong-path scripts. Write the generator locally, `scp` it, then run it on the host.
- Create the job from the runtime host:
  `hermes -p <profile> cron create "<expr>" --name <job> --skill <skill> --script <file>.py --deliver telegram`
- Test the wrapper itself before trusting the job (`python3 <wrapper>`), then `hermes cron run <job>`.
- `--no-agent` delivers the script's stdout verbatim with **no model turn**. That is a notification
  ping, not an agent. An agent job must not use it.

## Pitfalls

- Ensure SSH key is authorized on VPS (`~/.ssh/authorized_keys`) and that the VPS SSH port (2222) is accessible.
- When creating bot scripts on VPS, use proper variable quoting to avoid early expansion.
- `--no-agent` output is delivered directly with no model turn; an agent job needs the model, so
  check logs for success/failure instead of assuming the script's exit code is the whole story.
- If a bot script fails, inspect its log in `~/.hermes/logs` and fix the script before re-running.
- Keep webhook secret in sync between Hermes config and Sejoli plugin panel.

