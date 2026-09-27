---
name: messaging-platform-setup
description: "\"Setup Telegram platform in Hermes.\""
version: 1.0
author: Hermes Agent
category: integrations
---

# Setup Telegram

1. Install plugin: `hermes plugins install telegram`
2. Enable: `hermes config set plugins.enabled '["]telegram["]'`
3. Set token: `hermes config set telegram.token <TOKEN>`
4. Set webhook: `hermes config set telegram.webhook https://your.domain/webhooks/telegram`
5. Restart gateway: `hermes gateway restart`
6. Verify: `hermes logs | grep -i telegram`