---
name: hermes-model-provider-config
description: Set Hermes model/provider, clear overrides, restart gateway.
---
Use when configuring Hermes Agent model/provider settings, managing session overrides, setting API keys for Gemini or other LLMs, and restarting the gateway to apply changes.

- Always verify the current config.yaml and .env before making changes.
- To change model/provider: edit ~/.hermes/config.yaml under `model:` and `providers:`
- For Gemini, set `provider: google`, `base_url: https://generativelanguage.googleapis.com/v1beta/openai`, and add GEMINI_API_KEY and GEMINI_BASE_URL in ~/.hermes/.env (uncomment and fill).
- After editing config, restart the gateway: `systemctl --user restart hermes-gateway`.
- Clear any session overrides that cause model mismatches: delete offending rows from `gateway_routing` table in ~/.hermes/state.db, or delete ~/.hermes/sessions/sessions.json.
- Verify the gateway is active: `systemctl --user is-active hermes-gateway`.
- Test with a simple prompt: `hermes -z "Test: balas OK"`.
- If you see "Unsupported model mimo-auto", check for stray mimo references in config or environment and remove them.
- Keep the desktop and VPS in sync via the hermes-sync.sh script; run it manually after pushing config changes to GitHub.
