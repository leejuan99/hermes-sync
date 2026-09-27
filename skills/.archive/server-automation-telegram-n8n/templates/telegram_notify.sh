#!/bin/bash
# Usage: telegram_notify.sh "Message here"
# Sends message to Telegram bot

BOT_TOKEN="8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y"
CHAT_ID="316228407"
MESSAGE="$1"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d text="${MESSAGE}" \
  -d parse_mode="Markdown" > /dev/null