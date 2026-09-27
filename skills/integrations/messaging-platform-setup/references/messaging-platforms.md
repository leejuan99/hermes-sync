# Messaging Platforms Reference

## Telegram
- Bot token from @BotFather.
- Webhook must be public HTTPS.
- Toolset appears as `telegram` after enabling.
- Incoming updates have `update.message.chat.id`.
- Send: `hermes telegram send --to <chat_id> --text \"...\"`

## WhatsApp
- Pair via QR code; session in ~/.hermes/whatsapp/session.
- To unpair, delete that folder.

## Discord
- Enable Message Content Intent; token from Dev Portal.

## General
- Restart gateway after config changes.
- Check logs: `hermes logs | grep -i <platform>`.
