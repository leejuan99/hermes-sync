---
name: hermes-vps-config
description: Set up Hermes VPS for Telegram bot using Gemini model.
category: devops
version: 1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [vps, configuration, telegram, gemini]
    related_skills: []
---
## When to Use
You need to configure or reconfigure Hermes Agent on a VPS for Telegram bot, especially when changing model/provider, setting API keys, or clearing session overrides.

## Procedure
1. SSH into VPS: `ssh -p 2222 -i ~/.ssh/vps_key root@<VPS_IP>`
2. Check current config: `cat /root/.hermes/config.yaml`
3. Update model and provider as needed:
   - Edit `model.default` to desired model (e.g., `gemini-3.5-flash`)
   - Edit `provider` to match provider (e.g., `google`)
   - Ensure provider block exists under `providers:` with correct `base_url` and `key_env`.
4. Set API keys in `.env`:
   - Open `/root/.hermes/.env`
   - Uncomment and set the appropriate key line (e.g., `GEMINI_API_KEY=your_key`)
   - Set `GEMINI_BASE_URL` if needed.
5. Clear any session overrides that may cause model mismatches:
   - Remove `model_override` entries from `/root/.hermes/sessions/sessions.json` (delete the whole object) or set to null.
   - Update `sessions` table in `/root/.hermes/state.db`: set `model` and `model_config` to desired values for Telegram sessions.
6. Restart Hermes gateway: `systemctl --user restart hermes-gateway`
7. Verify service is active: `systemctl --user is-active hermes-gateway`
8. Test with a simple call: `hermes -z "Test: ping"` and check output.
9. If still errors, check logs: `tail -20 /root/.hermes/logs/agent.log`

## Pitfalls
- Forgetting to uncomment the API key line in `.env` leads to "Please pass a valid API key" errors.
- Leaving `model_override` in sessions.json or state.db causes the gateway to ignore config.yaml and use stale model, resulting in "Unsupported model" or provider mismatches.
- Using an incorrect `base_url` for the provider (e.g., OpenRouter URL for Gemini) yields 404 errors.
- Not restarting the gateway after config changes leaves old settings loaded.
- Assuming the default model is always available; verify model exists via provider's model list before setting.

## References
- `references/model-list-gemini.md` – how to list available Gemini models via API.
- `templates/hermes-config.yaml` – example config.yaml with provider blocks.
- `scripts/clear-session-overrides.sh` – script to reset session overrides.
