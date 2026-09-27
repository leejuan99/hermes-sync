#!/usr/bin/env bash
# Test Telegram bot via Hermes

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <chat_id>"
  exit 1
fi

CHAT_ID=$1
TOKEN=$(hermes config get telegram.token)

if [[ -z "$TOKEN" ]]; then
  echo "Error: telegram.token not set. Run:\n  hermes config set telegram.token YOUR_TOKEN"
  exit 1
fi

# Verify bot info
curl -s "https://api.telegram.org/bot$TOKEN/getMe" | jq .

# Send test message via Hermes
hermes send --to telegram:$CHAT_ID "Hello from Hermes test script!"

echo "Test message sent to chat $CHAT_ID"
