# Move Hermes Gateway (WhatsApp) From Desktop to VPS

When the user wants the bot online 24/7 without their PC on.

## Procedure

1. **Survey the target**: check free RAM/disk and `hermes --version` on both sides.
   Source and target versions must match — the Baileys session format is version-sensitive.
   Update the target first (`hermes update`).
2. **Transfer secrets without displaying them**: extract the value to a temp file,
   scp it to /tmp on the target, upsert server-side into the target `.env`, then shred
   temp files on both sides. Verify with redacted grep only — values must never enter
   chat output or logs.
3. **Copy the paired WhatsApp session** (`creds.json`, `identity-key-*.json`,
   `app-state-sync-key-*.json`, `lid-mapping-*.json`, `device-list-*.json`,
   `app-state-sync-version-*.json`; exclude `bridge.pid`) into the target's
   `whatsapp/session/` dir. A copied paired session skips QR re-pairing entirely.
4. **Carry the allowlist**: set `WHATSAPP_ALLOWED_USERS` to the sender phones AND LIDs
   (resolve LIDs via `lid-mapping-<LID>_reverse.json`). A bridge with the wrong allowlist
   connects fine but silently drops every message.
5. **Test model credentials on the target before cutover** (`hermes chat -q`):
   a paired bridge with no LLM credentials answers nothing.
6. **Cutover order — stop source first**: kill the source gateway AND its bridge process
   before starting the target. The same credentials active twice fight each other
   (reconnect loops, dropped messages).
7. **Start the target as a service** (`hermes gateway install` + `hermes gateway start`;
   enable linger so it survives logout), then verify `bridge.log` shows the expected
   `Allowed users` plus `WhatsApp connected!` and `gateway_state.json` reports connected.
8. **Port skills/memory/MCP**: copy missing skill dirs, `MEMORY.md`/`USER.md`
   (back up the target's copies first), merge the `mcp_servers` block into the target
   `config.yaml`; restart the gateway so MCP changes load.

## Pitfalls

- One active gateway per WhatsApp session. Before launching any gateway, check for an
  already-running instance — duplicates cause Telegram polling conflicts and WhatsApp
  session fights. The CLI refuses with `Another gateway instance is already running`;
  find the holder via process list (`gateway run` in the command line) and stop it first.
- Start long-lived daemons silent (no broad `error` notify patterns): a chatty gateway
  spams notifications until real signals drown. Kill stale watchers when they outlive
  their process.
