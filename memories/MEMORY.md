User: casual Indonesian (bray, lo/gua, gass, susah njir). Prefers GUI apps over CLI. Gets frustrated with complexity - wants quick action. Unfamiliar with dev basics - explain from scratch. Shared private SSH key in chat - educated on security. Windows, C:\Users\pc, Node 25.8.1, Edge non-standard path. Gets angry when things don't work ('bangsat lo!').
§
WhatsApp bot (Baileys, bot mode): bot number 6285218011693, owner personal 62817777616 / LID 36885279826005 — all three in WHATSAPP_ALLOWED_USERS. Gateway runs on local Windows PC (PC must stay on); Telegram platform disabled (webhook conflict).
§
User wants agent to execute/run things directly instead of giving manual step-by-step instructions; finds repeated manual setup a hassle.
§
User runs one-person company selling Coway air purifiers via Smart Millionaire platform. Uses WordPress (smartmillionaire.co.id) with Sejoli plugin for membership/affiliate. Hermes VPS + 9Router + WA bot for sales automation. Target: automate follow-up to purchasers via WA.
§
VPS 194.127.192.52 (GreenCloud SG, Ubuntu 22.04, aaPanel :26676, SSH :2222 key-only via ~/.ssh/vps_key) is the REAL 24/7 host: hermes-gateway systemd enabled + linger=yes, profile default, model openrouter/free, Telegram (chat_id 316228407) + WhatsApp Baileys. PC gateway is secondary — PC off = jobs die.
§
VPS had 5 FAKE marketing cron jobs (Keyword Research, Copy-Design, Ad-Scheduler, Analytics-Watcher, Content-Edu Bots): hardcoded captions, invented analytics, empty stdout so nothing ever delivered. Paused 2026-09-29. Always read ~/.hermes/scripts/*.sh before trusting a job's name.
§
VPS sosmed division: skill `sosmed-coway`, board `sosmed`, prompts ~/.hermes/marketing/prompts/, wrappers ~/.hermes/scripts/sosmed_*.py. 6 cron jobs --deliver telegram: trend-scout 07:00, content-planner Mon 08:00, content-writer 09:00, visual-brief 10:00, analytics-reporter 20:00, community-manager */30 8-20 Mon-Sat. Delivery verified.
§
Windows profile `sosmed` cloned but unused (production is the VPS). hermes-home-dashboard desktop plugin removed from ~/AppData/Local/hermes/desktop-plugins/.