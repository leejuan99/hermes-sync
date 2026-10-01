User: casual Indonesian (bray, lo/gua, gass, susah njir). Prefers GUI over CLI, wants quick action, execute directly instead of manual step-by-step. Unfamiliar with dev basics - explain from scratch. Windows, C:\Users\pc, Node 25.8.1, Edge. Shared private SSH key in chat - educated on security. Gets angry when things don't work.
§
WhatsApp bot (Baileys, bot mode): bot 6285218011693, owner 62817777616 / LID 36885279826005 — all in WHATSAPP_ALLOWED_USERS.
§
User runs one-person company selling Coway air purifiers via Smart Millionaire. WordPress (smartmillionaire.co.id) + Sejoli plugin for membership/affiliate. Target: automate follow-up to purchasers via WA.
§
VPS 194.127.192.52 (GreenCloud SG, Ubuntu 22.04, aaPanel :8888 admin_path=/, SSH :2222 key-only ~/.ssh/vps_key) is the REAL 24/7 host: hermes-gateway = systemd USER unit + linger=yes, profile default, runs the bots. PC gateway is secondary — PC off = jobs die.
§
VPS old cron jobs were FAKE (hardcoded captions, invented analytics). Paused. Always read ~/.hermes/scripts/* before trusting a job name.
§
VPS sosmed division: skill sosmed-coway, prompts ~/.hermes/marketing/prompts/, now superseded by profile dm (DM division, skill dm-coway, 8 agents dm-*).
§
Sync desktop↔VPS via GitHub leejuan99/hermes-sync (skills/ memories/ plugins/ SOUL.md only; config.yaml & .env stay per-machine). Desktop = config surface, VPS = runtime. Auto-pull cron on both.
§
Novamira WP MCP: sandbox wp-content/novamira-sandbox/ auto-loads ALL .php alphabetically; any echo/print pollutes the JSON-RPC stream → all MCP tools fail with 'jsonrpc version must be 2.0'.
§
VPS gateway: multiplex_profiles=true → ticks default+dm (verify: grep 'tick N profile(s) under multiplex' gateway.log). Each profile needs its OWN bot token — token lock blocks sharing one Telegram token. `hermes -p X cron status` false-negatives under multiplex.
§
VPS model = openrouter/deepseek-v3.2. OpenRouter credits are the single point of failure: HTTP 402 'requires more credits' killed 61 cron runs. Check errors.log for 402 before debugging anything else.