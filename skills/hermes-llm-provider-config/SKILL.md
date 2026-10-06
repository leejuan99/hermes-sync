---
name: hermes-llm-provider-config
category: integrations
description: Set Hermes LLM provider/model for Telegram bot on VPS.
---
## Procedure

1. **Choose model and provider**
   - Example for Gemini via Google’s OpenAI‑compatible endpoint:
     ```yaml
     model:
       default: gemini/gemini-1.5-pro
       provider: google
     ```
   - Provider block must match the chosen provider:
     ```yaml
     providers:
       google:
         base_url: https://generativelanguage.googleapis.com/v1beta/openai
         key_env: GEMINI_API_KEY
     ```
   - If using OpenRouter, keep `provider: 9router` or `provider: openrouter` and adjust `base_url` and `key_env` accordingly.

2. **Edit `~/.hermes/config.yaml`**
   - Open the file with your preferred editor (e.g., `nano ~/.hermes/config.yaml`).
   - Locate the `model:` section and set `default` and `provider` as chosen.
   - Locate (or add) the `providers:` section and insert/update the block for your provider with correct `base_url` and `key_env`.
   - Save and exit.

3. **Set API key in `~/.hermes/.env`**
   - Open `~/.hermes/.env`.
   - Find the lines for your provider (e.g., `# GEMINI_API_KEY=your_gemini_key_here` and `# GEMINI_BASE_URL=...`).
   - Remove the leading `#` to uncomment and replace the placeholder with the actual key.
   - Ensure no extra spaces or quotes unless required.
   - Save.

4. **Clear any session overrides** (prevents the bot from sticking to a stale model)
   - **Option A – Remove sessions file** (simplest):
     ```bash
     mv ~/.hermes/sessions/sessions.json ~/.hermes/sessions/sessions.json.bak-$(date +%s)
     ```
   - **Option B – Clear via SQLite** (if you prefer to keep the file):
     ```bash
     sqlite3 ~/.hermes/state.db "UPDATE sessions SET model_override = NULL WHERE source = 'telegram';"
     ```
   - If using Option A, the gateway will create a fresh sessions.json on next start.

5. **Restart the Hermes gateway** to apply changes
   ```bash
   systemctl --user restart hermes-gateway
   ```
   - Wait a few seconds, then confirm it’s active:
     ```bash
     systemctl --user is-active hermes-gateway
     # should output 'active'
     ```

6. **Verify the configuration**
   - Run a quick test via Hermes CLI:
     ```bash
     hermes -z "Test: ping" 2>&1 | head -5
     ```
   - Expected output: a short response (e.g., "OK bray, gass.") without provider errors like "HTTP 404: No active credentials" or "Model provider failed after retries".
   - If you see errors, repeat steps 2‑4, ensuring the `.env` key is present and the `base_url` is correct.

7. **Telegram bot session reset** (optional but recommended)
   - In your Telegram chat with `@hermesLJ99Bot`, send the command `/new` to force a fresh conversation session, ensuring any cached model_override is cleared.

## Pitfalls
- **Failing to uncomment the API key in `.env`** leaves the provider without credentials, resulting in errors like "HTTP 404: No active credentials for provider: openai" or generic provider‑failed messages.
- **Incorrect `base_url`** (e.g., using the non‑OpenAI‑compatible Gemini endpoint) causes 404/400 errors from the provider.
- **Not clearing session overrides** makes the bot continue to use a stale model_override stored in `sessions.json` or `state.db`, so even after fixing config.yaml the bot may still attempt the old model and fail.
- **Restarting the gateway before saving edits** means the changes are not picked up; always edit first, then restart.
- **Using a free `:‑free` model** that is not available in your provider’s quota leads to HTTP 400/500 errors; prefer a stable model tag (e.g., `gemini/gemini-1.5-pro`).
- **Forgetting to set `provider` to match the provider block** (e.g., setting `default: gemini/...` but leaving `provider: 9router`) will cause the agent to look for the wrong provider block and fail.

## Verification
After completing the steps, send any message to the Telegram bot. It should respond using the newly configured model without provider‑related errors. If the bot still appears broken, check the gateway logs:
```bash
journalctl --user-unit hermes-gateway -f
```
Look for lines containing "provider failed" or "model provider failed" and address the indicated issue (usually missing key or wrong URL).

## Assistant‑driven execution

If you provide the Gemini API key, the assistant can perform the remaining steps automatically:

1. Share your Gemini API key in this chat (it will be stored only for this operation and not persisted).
2. The assistant will:
   - Uncomment and set `GEMINI_API_KEY` and `GEMINI_BASE_URL` in `~/.hermes/.env`.
   - Clear session overrides (`sessions.json` backup and SQLite update).
   - Restart the Hermes gateway.
   - Run a quick test to confirm the bot responds.

After that, you can test the bot directly in Telegram.

## References
- For Gemini API key creation: https://makersuite.google.com/app/apikey
- OpenRouter model list: https://openrouter.ai/models

