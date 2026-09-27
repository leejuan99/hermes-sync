#!/bin/bash
# /root/telegram_notify.sh
# Send message via Telegram Bot API

BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
CHAT_ID="YOUR_CHAT_ID_HERE"
MESSAGE="$1"

# URL encode the message
MESSAGE_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$MESSAGE'''))" 2>/dev/null)

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d parse_mode="Markdown" \
  -d text="${MESSAGE_ENCODED}" \
  > /dev/null

echo "Notification sent"