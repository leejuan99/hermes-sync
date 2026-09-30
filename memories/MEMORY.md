User: casual Indonesian (bray, lo/gua, gass, susah njir). Prefers GUI over CLI, wants quick action, execute directly instead of manual step-by-step. Unfamiliar with dev basics - explain from scratch. Windows, C:\Users\pc, Node 25.8.1, Edge. Shared private SSH key in chat - educated on security. Gets angry when things don't work.
§
WhatsApp bot (Baileys, bot mode): bot 6285218011693, owner 62817777616 / LID 36885279826005 — all in WHATSAPP_ALLOWED_USERS.
§
User runs one-person company selling Coway air purifiers via Smart Millionaire. WordPress (smartmillionaire.co.id) + Sejoli plugin for membership/affiliate. Target: automate follow-up to purchasers via WA.
§
VPS 194.127.192.52 (GreenCloud SG, Ubuntu 22.04, aaPanel :8888 admin_path=/, SSH :2222 key-only ~/.ssh/vps_key) is the REAL 24/7 host: hermes-gateway = systemd USER unit + linger=yes, profile default, runs the bots. PC gateway is secondary — PC off = jobs die.
§
VPS had 5 FAKE marketing cron jobs (hardcoded captions, invented analytics, empty stdout). Paused 2026-09-29. Always read ~/.hermes/scripts/*.sh before trusting a job's name.
§
VPS sosmed division: skill sosmed-coway, board sosmed, prompts ~/.hermes/marketing/prompts/, wrappers ~/.hermes/scripts/sosmed_*.py, 6 cron jobs --deliver telegram (trend-scout 07:00, planner Mon 08:00, writer 09:00, visual-brief 10:00, analytics 20:00, community */30 8-20 Mon-Sat).
§
Sync desktop↔VPS via GitHub leejuan99/hermes-sync (skills/ memories/ plugins/ SOUL.md only; config.yaml & .env stay per-machine). Desktop = config surface, VPS = runtime. Auto-pull cron on both.
§
Novamira WP MCP: sandbox wp-content/novamira-sandbox/ auto-loads ALL .php alphabetically; any echo/print pollutes the JSON-RPC stream → all MCP tools fail with 'jsonrpc version must be 2.0'.