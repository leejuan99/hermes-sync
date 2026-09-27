# WhatsApp Gateway Setup (Baileys) — VPS Quick Reference

Complete setup flow for running Hermes WhatsApp gateway on a headless VPS (Ubuntu 22.04, aaPanel, GreenCloud Singapore).

---

## Prerequisites

- VPS with SSH key-only auth (port 2222, GreenCloud external firewall)
- Root access via SSH key (`~/.ssh/vps_key` in this environment)
- Domain/subdomain pointed to VPS (for webhook URL if needed)

---

## 1. Install Hermes on VPS

```bash
ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 \
  "curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
```

Installs to `/usr/local/lib/hermes-agent`, command at `/usr/local/bin/hermes`, data at `/root/.hermes/`.

---

## 2. Configure Gateway + WhatsApp (Baileys)

```bash
ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 "hermes gateway setup"
```

Interactive wizard:
- Select **26** (WhatsApp)
- Enable → `Y`
- Allowed users → `*` (anyone) or comma-separated phone numbers
- Home chat ID → leave empty
- Done → **27**
- Start gateway now → `Y`
- Install as service → `Y`
- Choose **1** (User service, linger enabled)

---

## 3. Pair WhatsApp (Interactive — Requires TTY)

**Cannot run via piped stdin.** Must use `tmux` with allocated PTY:

```bash
# On VPS, start pairing in tmux session
ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 -t \
  "tmux new-session -d -s whatsapp_pair 'hermes whatsapp'"

# Send choices
ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 \
  "tmux send-keys -t whatsapp_pair '1' Enter"   # Mode: separate bot number

ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 \
  "tmux send-keys -t whatsapp_pair '*' Enter"   # Allow all users

# Watch QR code (refreshes every few seconds)
ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 \
  "tmux capture-pane -t whatsapp_pair -p"
```

### On Phone (WhatsApp):
1. Open WhatsApp → **3 dots** → **Linked devices** → **Link a device**
2. Scan QR code displayed in terminal
3. Terminal shows "Connected!" / "Paired!" → gateway auto-restarts

---

## 4. Verify Gateway Running

```bash
ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 "hermes gateway status"
```

Expected:
```
● hermes-gateway.service - Hermes Agent Gateway
     Active: active (running) since ...
     ...
✓ whatsapp: Paired and connected
```

---

## 5. Test Message

Send a WhatsApp message to the bot number → Hermes replies in chat.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `hermes whatsapp` says "requires interactive terminal" | Use `tmux` as shown above |
| QR code not scanning / too small | Zoom terminal (Ctrl++), or run `hermes whatsapp` locally then copy session |
| Gateway stuck "activating (auto-restart)" | WhatsApp not paired yet — complete pairing |
| Service dies on logout | `loginctl enable-linger root` (already done by installer) |
| `permission denied` on SSH | Use correct key: `~/.ssh/vps_key` not `id_ed25519` |
| Port 22 blocked | GreenCloud firewall → add rule for port 2222 in panel |
| **Allowlist mismatch — messages ignored** | User's LID not in allowlist. Check `lid-mapping-*_reverse.json` in session dir. Add LID + phone to `WHATSAPP_ALLOWED_USERS` in `.env` + restart gateway |
| **Bridge restarts with code 515/440 (conflict)** | Another instance holding session. Kill old bridge: `pkill -f bridge.js` then restart gateway |
| **Gateway connected but no replies** | Check `bridge.log` for `allowlist_mismatch`. WhatsApp uses LID (`36885279826005@lid`) not phone. Add LID to allowlist |

---

## Gateway / SSH Executor Architecture (24/7 vs Local)

When a user expects messaging functions (Telegram, WhatsApp relay) to work continuously independent of their local PC, treat this as a **VPS-hosted gateway requirement**, not a local auto-start issue.

**Verified architecture (`request_dump_20260810_235535_7b6329`):**
- SSH key path: `~/.ssh/vps_key` (port 2222, key-only auth)
- Remote SSH executor: `/root/ssh_executor.py` listens on `localhost:5679` (`netstat -tlnp | grep 5679` confirms `LISTEN` when running)
- Remote webhook endpoint: `https://n8n.smartmillionaire.co.id/webhook/telegram/webhook` (n8n responds independently)
- Bot endpoint: Telegram bot (`@hermesLJ99Bot`, token `8871187293:...`) sends to the webhook; gateway handles relay

**Deployment check (before diagnosing Telegram failure):**
```bash
# 1. Confirm SSH access
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 'uptime'

# 2. Confirm SSH executor is LISTENING (not just gateway running locally)
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 'netstat -tlnp | grep 5679'

# 3. Confirm webhook responds independently of gateway state
curl -s -X POST https://n8n.smartmillionaire.co.id/webhook/telegram/webhook \
  -H 'Content-Type: application/json' \
  -d '{"message":{"message_id":1,"text":"/status"}}'
```

**Pitfall — Gateway missing locally vs not deployed on VPS:**
The local startup entry (`Hermes_Gateway` in `HKCU\...\Run`) and the local service (`hermes-gateway`) are separate from VPS deployment. Removing the startup entry disables local auto-start; missing the service binary (`.vbs`, service unit) means no gateway runs at all. Before assuming 24/7 operation, verify both: `sc query hermes-gateway` locally, and `netstat | grep 5679` remotely. A running gateway on a local PC that must stay on is NOT a 24/7 solution.

**Pitfall — SSH timeout is not unreachable:** If `ssh` returns exit 124 (timeout), the VPS may still be reachable (`ping -c 2 194.127.192.52` succeeds at 16ms). A timeout indicates stalled negotiation or firewall drop, not total unavailability. Confirm with `ping` independently before diagnosing gateway failure.

**Pitfall — Telegram disabled despite working infrastructure:** Even when gateway, SSH executor, and webhook all respond, Telegram will not reply if the gateway config or webhook subscription is disabled (`Telegram platform disabled` due to webhook conflict). Confirm webhook independently (`curl`) before diagnosing Telegram failure, and reset webhook conflicts explicitly (`hermes gateway restart`) before enabling Telegram.

---

## Key Paths on VPS

| Path | Purpose |
|------|---------|
| `/usr/local/bin/hermes` | Main command |
| `/root/.hermes/config.yaml` | Gateway + platform config |
| `/root/.hermes/.env` | API keys + `WHATSAPP_ALLOWED_USERS` |
| `/root/.hermes/logs/gateway.log` | Gateway logs |
| `/root/.config/systemd/user/hermes-gateway.service` | Systemd unit |
| `/root/.hermes/whatsapp/session/` | Baileys session (creds.json, lid-mapping-*.json) |

---

## Allowlist Configuration (Critical)

Baileys uses **LID (Linked Identity)** internally, not just phone numbers.

### Where to find LIDs
```bash
ls /root/.hermes/whatsapp/session/lid-mapping-*_reverse.json
# Example: lid-mapping-36885279826005_reverse.json → contains "62817777616"
```

### Format for WHATSAPP_ALLOWED_USERS
```bash
# .env
WHATSAPP_ALLOWED_USERS=+6285218011693,62817777616,36885279826005
#           (bot number)     (phone)      (LID)
```

**Must include all three** for the bridge to accept messages from that user.

### After editing .env — restart BOTH bridge and gateway
```bash
pkill -f bridge.js
hermes gateway restart
```

---

## Session Persistence (No Re-pairing)

Session files to copy for migration:
```bash
scp /root/.hermes/whatsapp/session/creds.json \
    /root/.hermes/whatsapp/session/identity-key-*.json \
    /root/.hermes/whatsapp/session/lid-mapping-*.json \
    /root/.hermes/whatsapp/session/device-list-*.json \
    /root/.hermes/whatsapp/session/app-state-sync-*.json \
    target:/root/.hermes/whatsapp/session/
```

---

## Commands Cheatsheet

```bash
hermes gateway status        # Check status
hermes gateway start/stop    # Control service
hermes gateway restart       # Restart
journalctl --user -u hermes-gateway -f  # Live logs
hermes whatsapp              # Re-pair (interactive, tmux required)
hermes gateway setup         # Reconfigure platforms
pkill -f bridge.js           # Kill stuck bridge
```

---

## Notes for This Environment

- **SSH key**: `~/.ssh/vps_key` (not default `id_ed25519`)
- **SSH port**: 2222 (GreenCloud external firewall blocks 22)
- **VPS IP**: 194.127.192.52
- **aaPanel**: https://server.smartmillionaire.co.id:26676/a83a1c60
- **WordPress**: smartmillionaire.co.id/smart-webinar/ (Novamira MCP + smart-webinar plugin)
- **User prefers**: casual Indonesian, GUI over CLI, quick action ("gass")