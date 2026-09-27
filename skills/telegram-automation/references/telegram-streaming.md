# Telegram Streaming Option

The `platforms.telegram.streaming` setting in Hermes config controls whether the Telegram plugin uses streaming updates (long‑polling with idle connection) or standard polling via `getUpdates`.

## When to disable streaming

- If you experience missing inbound logs after a gateway restart.
- If you see duplicate messages or the bot appears unresponsive.
- When running Hermes on Windows or in environments where long‑held connections are blocked by firewalls or proxies.
- When you rely on the gateway’s housekeeping and kanban dispatcher intervals; streaming can interfere with periodic logging.

## How to verify

After setting `platforms.telegram.streaming false` and restarting the gateway, check the logs for lines like:

```
2026-09-21 09:24:37,609 INFO hermes_plugins.telegram_platform.adapter: [Telegram] Telegram polling confirmed healthy: getUpdates progressing (generation 1)
```

If streaming is enabled, you will see instead:

```
2026-09-21 09:24:37,609 INFO hermes_plugins.telegram_platform.adapter: [Telegram] Connected to Telegram (streaming mode)
```

## Recommendation

For most VPS setups with a public webhook, keep streaming disabled unless you have a specific need for low‑latency streaming updates and have verified that your network allows persistent connections to Telegram’s servers.
