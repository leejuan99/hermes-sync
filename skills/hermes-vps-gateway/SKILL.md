---
name: hermes-vps-gateway
description: "Use when needing 24/7 Telegram bot. Run Hermes on VPS."
version: 1.0
author: Hermes Agent
category: devops
platforms: [linux]
---
# Hermes VPS Gateway Deployment for Persistent Telegram Bot

## Overview
Class-level skill for setting up Hermes Agent gateway on a VPS (e.g., GreenCloud Ubuntu 22.04 with aaPanel) so that the Telegram bot remains online 24/7, independent of the local PC's power state.

## Triggers
- User wants Telegram bot to stay active even when local computer is off.
- Need to run Hermes gateway as a background service on VPS.
- Configure Telegram bot token and allowed users for VPS-based Hermes.

## Core Knowledge

### Prerequisites
- SSH access to VPS (port 2222, key-only auth).
- VPS running Ubuntu 22.04 with aaPanel (or similar).
- GreenCloud external firewall must allow inbound TCP 2222 (SSH) and optionally 26676 (aaPanel) if needed.
- Telegram bot token (from @BotFather) and user ID (chat ID) ready.

### Procedure

1. **Ensure SSH connectivity**
   Verify port 2222 is open in GreenCloud firewall.
   Test connection:
   ```bash
   ssh -i ~/.ssh/vps_key -p 2222 pc@194.127.192.52 "echo SSH OK"
   ```

2. **Install Hermes on VPS**
   Log in to VPS and run the official installer:
   ```bash
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
   ```
   This sets up Python, uv, virtualenv, and the `hermes` command.

3. **Configure Telegram bot credentials**
   Edit (or create) `~/.hermes/.env` on the VPS:
   ```bash
   # Replace with your actual bot token and user ID
   echo 'TELEGRAM_BOT_TOKEN=8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y' >> ~/.hermes/.env
   echo 'TELEGRAM_ALLOWED_USERS=316228407' >> ~/.hermes/.env
   ```
   Ensure the file is readable only by the user (`chmod 600 ~/.hermes/.env`).

4. **Enable Telegram platform and disable conflicting services**
   To avoid gateway crashes due to missing `API_SERVER_KEY`, disable the API server platform (optional but recommended for a minimal gateway):
   ```bash
   hermes config set platforms.telegram.enabled true
   hermes config set platforms.api_server.enabled false
   ```
   Verify configuration:
   ```bash
   hermes config
   ```

5. **Start the gateway as a persistent service**
   **Option A: Install as autostart service (recommended)**
   ```bash
   hermes gateway install
   # This creates a service that starts on boot and runs in the background.
   ```
   **Option B: Run inside `screen` or `tmux` for manual logging**
   ```bash
   screen -S hermes_gateway
   hermes gateway run
   # Press Ctrl+A D to detach from the session, leaving it running.
   ```

6. **Verify the gateway is running**
   ```bash
   hermes gateway status
   # Expected output: "Gateway process running" with a PID.
   ```
   Check logs if needed:
   ```bash
   tail -f ~/.hermes/logs/gateway.log
   ```

7. **Test from local PC**
   Open Telegram, message your bot (`@hermesLJ99Bot` or whatever username you set).
   The bot should respond via the VPS-hosted gateway.

## Pitfalls to Avoid

- **External firewall blocks SSH**: GreenCloud VPS has an external firewall that overrides UFW/aaPanel. Always open port 2222 in the GreenCloud panel, not just in `ufw`.
- **API server crash**: Leaving `platforms.api_server.enabled: true` without setting `API_SERVER_KEY` causes the gateway to exit immediately on startup. Disable it unless you have a key.
- **Missing `TELEGRAM_ALLOWED_USERS`**: Without this, the bot ignores all messages (security feature). Add your numeric user ID.
- **Using old bot token**: If you rotated the bot token, update `.env` and restart the gateway; otherwise it connects to the defunct bot.
- **Key permissions**: Ensure the SSH private key (`vps_key`) is `chmod 600`; otherwise SSH will refuse to use it.
- **Service not persisting**: After `hermes gateway install`, verify the service is enabled: `systemctl --user status hermes-gateway` (or check Windows‑style service if applicable).

## Verification

After deployment, the bot should remain responsive even when you shut down your local PC. You can confirm by:
1. Turning off your local computer.
2. Sending a message to the bot from another device (or wait and send later).
3. Observing that the bot replies (possibly after a short delay if the gateway needed to restart).

## Related Skills

- `vps-server-admin` – for general VPS/aaPanel management, SSH hardening, and debugging.
- `hermes-agent` – for core Hermes configuration, model selection, and advanced features.
- `terminal` – for SSH and command‑execution fundamentals.

## Version
1.0 – Initial creation based on session deploying Hermes gateway on GreenCloud VPS for persistent Telegram bot.
