---
name: hermes-webhook-automation
description: Use when automating webhook actions. Hermes validates.
category: integrations
---
# Hermes Webhook Automation

## When to Use
Use this skill when you need to automate actions (e.g., send WhatsApp messages, log to CRM) triggered by webhooks from platforms like Sejoli, WooCommerce, or similar services.

## Prerequisites
- Hermes Agent running and reachable via a public URL.
- A strong secret string (>=32 chars) for HMAC‑SHA256 signature verification.
- WhatsApp bot configured in Hermes (if sending WA messages).

## Step‑by‑step Procedure

1. **Prepare the webhook endpoint URL**
   - Ensure Hermes gateway is running and its webhook receiver is exposed at a fixed URL, e.g.
     `https://<your-domain>/webhooks/<name>`
   - If using a VPS with aaPanel/OpenLiteSpeed, set up a reverse proxy to forward the URL to Hermes’ local webhook port (default 8644).
   - Obtain or generate a secret string.

2. **Configure the secret in Hermes**
   - Edit `~/.hermes/config.yaml` and set under `webhook:`:
     ```yaml
     webhook:
       enabled: true
       extra:
         port: 8644
         secret: <YOUR_SECRET>
     ```
   - Restart the Hermes gateway: `systemctl --user restart hermes-gateway` (or `hermes gateway run`).

3. **Create the webhook subscription in Hermes**
   - Run:
     ```bash
     hermes webhook subscribe <name> \
       --secret <YOUR_SECRET> \
       --events <event_name> \
       --prompt "<YOUR_PROMPT>" \
       --deliver prompt
     ```
   - Replace:
     - `<name>`: identifier, e.g., `sejoli-order`
     - `<YOUR_SECRET>`: the secret from step 1
     - `<event_name>`: the event key sent by the platform (e.g., `order.completed`)
     - `<YOUR_PROMPT>`: natural‑language instruction that Hermes will follow when the event arrives. Use placeholders that match payload keys, e.g.
       ```
       Extract from payload: customer_phone, customer_name, product_name, order_id, amount.\n       Then send a WhatsApp message to customer_phone with text: 'Halo {customer_name}, terima kasih telah membeli {product_name}. Pesanan Anda {order_id} telah selesai. Untuk pertanyaan, hubungi kami di 6285218011693.'
       ```
   - Verify output shows correct URL, secret, events, and deliver method.

4. **Set up the platform’s webhook**
   - In the platform’s admin UI (e.g., Sejoli → Webhooks), add a new webhook:
     - URL: the public URL from step 1
     - Secret: same as Hermes secret
     - Event(s): select the event you subscribed to
   - Save and use the platform’s “Test” button to send a sample payload.

5. **Validate signature and event handling**
   - Check Hermes gateway log:
     ```bash
     tail -f /root/.hermes/logs/gateway.log
     ```
   - Successful request shows:
     ```json
     {"status":"accepted","event":"<event_name>",...}
     ```
   - If you see `{"error":"Invalid signature"}`, double‑check secret match and payload integrity.

6. **Verify the action**
   - Ensure the WhatsApp bot receives the message as defined in the prompt.
   - If using a skill or MCP for CRM logging, confirm the entry appears.

## User Preferences (Embedded)
- **Execute directly**: Provide the exact commands to run; avoid lengthy explanations unless asked.
- **Minimal explanation**: Give only essential steps and short notes.
- **Quick action**: When user says “gass” or shows urgency, skip optional verification and go straight to core command.
- **GUI over CLI**: If a setting can be changed via aaPanel, WordPress admin, or Hermes desktop UI, mention that as preferred path before falling back to CLI.
- **Exact paths and commands**: Always give absolute paths (e.g., `/root/.hermes/config.yaml`) and the exact command to copy‑paste.

## Common Pitfalls
- **Secret mismatch**: HMAC secret must be byte‑for‑byte identical between Hermes and platform; any extra whitespace or newline causes signature failures. *Always copy‑paste the secret without modification.*
- **URL not reachable**: If Hermes is behind a firewall or proxy mis‑forwards, platform gets 404/502 and Hermes never sees request. *Test endpoint with curl from an external machine before configuring the platform.*
- **Event name mismatch**: Platforms may send `event_type` or nested structures; Hermes looks for top‑level `event` field unless prompt extracts otherwise. *Inspect a test payload (via platform test or logs) to confirm exact key names.*
- **Prompt placeholders not found**: If prompt references a key absent in payload, Hermes will still run but message will contain literal placeholder. *Verify payload keys from a test delivery.*
- **WhatsApp gateway not running**: If Hermes gateway process is down, webhook acceptance succeeds but no outbound WA message is sent. *Keep gateway running as a service (`hermes gateway run` or systemd).

## Reference Files
- `references/sample-payload.json` – example Sejoli order.completed payload for testing.
- `templates/webhook-subscription.json` – starter subscription file you can edit and load with `hermes webhook subscribe --file`.

