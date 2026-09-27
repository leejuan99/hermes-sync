---
name: telegram-automation
description: Set up and test a Telegram bot with Hermes Agent.
---

# Telegram Automation with Hermes

Use when you need to set up and test a Telegram bot via Hermes Agent, including installing the telegram-messaging skill, configuring webhook, sending/receiving messages, and integrating with cron jobs.

## Procedure

1. Install the telegram-messaging skill:
   ```
   hermes skills install clawhub/telegram-messaging --yes
   ```

2. Enable the telegram plugin in Hermes config:
   ```
   hermes config set plugins.enabled '["telegram-business"]'
   ```
   (Note: the skill provides the platform as `telegram-business`.)

3. Restart the Hermes gateway to load the plugin:
   ```
   hermes gateway restart
   ```

4. Set your Telegram bot token (obtain from BotFather):
   ```
   hermes config set telegram.token <YOUR_TOKEN>
   ```

5. Configure the webhook URL (ensure it's publicly reachable, e.g., via your VPS domain):
   ```
   hermes config set telegram.webhook_url https://your-domain.com/webhooks/telegram
   ```

6. **(Recommended) Disable streaming for more reliable polling:**
   ```
   hermes config set platforms.telegram.streaming false
   ```
   Then restart the gateway again:
   ```
   hermes gateway restart
   ```

7. Verify the bot info via Telegram API (optional):
   ```
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

8. Test sending a message via Hermes:
   ```
   hermes send --to telegram:<chat_id> "Test message"
   ```

9. To receive messages, ensure the webhook is correctly set up and check Hermes logs for updates:
   ```
   hermes logs | grep -i telegram
   ```

10. Integrate with cron jobs: create scripts in `~/.hermes/scripts/` and schedule with `hermes cron create`.

## Pitfalls

- Always restart the gateway after changing `plugins.enabled`; otherwise the new platform will not be loaded.
- The telegram-messaging skill registers the platform as `telegram-business`, not `telegram`. Use the correct name in config.
- Webhook URL must be accessible from Telegram servers (publicly reachable, valid SSL certificate).
- Keep the bot token secret; never expose it in logs or shared files.
- If you encounter "Permission denied (publickey)" when SSHing to VPS, ensure your SSH key is loaded into ssh-agent or specify the key with `-i`.
- **Streaming pitfall:** Leaving `platforms.telegram.streaming` set to `true` can cause the bot to appear unresponsive because Hermes may use streaming updates while the gateway also polls via `getUpdates`, leading to conflicts. Symptoms include no inbound logs after restart or duplicate messages. Set streaming to `false` and restart the gateway to resolve.

## References

- See `references/telegram-bot-token.md` for details on obtaining a token from BotFather.
- See `scripts/test-telegram-bot.sh` for a ready-to-run verification script.
- See `references/telegram-streaming.md` for an explanation of the streaming option and when to disable it.
