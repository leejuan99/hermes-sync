# WhatsApp | Hermes Agent
URL: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/whatsapp

WhatsApp | Hermes Agent

# WhatsApp Setup

Hermes connects to WhatsApp through a built-in bridge based on Baileys. This works by emulating a WhatsApp Web session â not through the official WhatsApp Business API. No Meta developer account or Business verification is required.

> Run `hermes gateway setup` and pick WhatsApp for a guided walk-through.

Two WhatsApp integrations

This page is for the Baileys bridge â quick to set up, personal accounts, no public URL needed, ban risk.

If you're running a real business bot and want stability, see the WhatsApp Business Cloud API guide instead. It's the official Meta-supported path: no account ban risk, but requires a Meta Business account and a public webhook URL.

The two adapters can also run in parallel against different phone numbers if you have a reason to.

Unofficial API â Ban Risk

WhatsApp does not officially support third-party bots outside the Business API. Using a third-party bridge carries a small risk of account restrictions. To minimize risk:

- Use a dedicated phone number for the bot (not your personal number)
- Don't send bulk/spam messages â keep usage conversational
- Don't automate outbound messaging to people who haven't messaged first

WhatsApp Web Protocol Updates

WhatsApp periodically updates their Web protocol, which can temporarily break compatibility with third-party bridges. When this happens, Hermes will update the bridge dependency. If the bot stops working after a WhatsApp update, pull the latest Hermes version and re-pair.

## Two Modesâ

| Mode | How it works | Best for |
| --- | --- | --- |
| Separate bot number (recommended) | Dedicate a phone number to the bot. People message that number directly. | Clean UX, multiple users, lower ban risk |
| Personal self-chat | Use your own WhatsApp. You message yourself to talk to the agent. | Quick setup, single user, testing |

## Prerequisitesâ

- Node.js v18+ and npm â the WhatsApp bridge runs as a Node.js process
- A phone with WhatsApp installed (for scanning the QR code)

Unlike older browser-driven bridges, the current Baileys-based bridge does not require a local Chromium or Puppeteer dependency stack.

## Step 1: Run the Setup Wizardâ

hermes whatsapp 

The wizard will:

1. Ask which mode you want (bot or self-chat)
2. Install bridge dependencies if needed
3. Display a QR code in your terminal
4. Wait for you to scan it

To scan the QR code:

1. Open WhatsApp on your phone
2. Go to Settings â Linked Devices
3. Tap Link a Device
4. Point your camera at the terminal QR code

Once paired, the wizard confirms the connection and exits. Your session is saved automatically.

tip

If the QR code looks garbled, make sure your terminal is at least 60 columns wide and supports Unicode. You can also try a different terminal emulator.

## Step 2: Getting a Second Phone Number (Bot Mode)â

For bot mode, you need a phone number that isn't already registered with WhatsApp. Three options:

| Option | Cost | Notes |
| --- | --- | --- |