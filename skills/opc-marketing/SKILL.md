---
name: opc-marketing
description: "Use when automating OPC marketing with Hermes Agent."
version: 0.1.0
---

# OPC Marketing Workflow with Hermes Agent

## 1. Webhook Subscription for External Events

When an external service (e.g., Sejoli, WooCommerce, Shopify) sends a webhook on events like `order.completed`, you can let Hermes ingest, validate, and act on it.

### Steps
1. **Obtain the shared HMAC secret** from the external service’s webhook settings.
2. **Create the subscription** in Hermes:
   ```
   hermes webhook subscribe <name> --secret <HMAC_SECRET> --events <event> --prompt "<prompt_instructions>" --deliver prompt
   ```
   - `<prompt_instructions>` should extract fields from the payload (e.g., `customer_phone`, `customer_name`, `product_name`, `order_id`, `amount`) and describe the action (send WhatsApp message, log to CRM, create a Kanban card).
   - Use `--deliver prompt` so the agent runs the prompt on each valid event.
3. **Verify** the subscription:
   ```
   hermes webhook list
   ```
4. **Test** with a valid signature:
   - Build a JSON payload matching the expected event.
   - Compute `sha256=HMAC(secret, payload)`.
   - Send `POST https://<your-domain>/webhooks/<name>` with header `X-Sejoli-Signature: <sha256>` and the JSON body.
   - Check `~/.hermes/logs/gateway.log` for `"status":"accepted"`.

### Pitfalls
- **Secret handling** – Never embed the secret in a shell script that gets echoed; pass it directly via `--secret` to avoid interpolation or logging.
- **Payload shape** – If the external service nests data under different keys, adjust the prompt accordingly; test with a sample payload first.
- **Duplicate processing** – Hermes will process every verified request; ensure your prompt is idempotent or store processed IDs in memory (`hermes memory add …`) if needed.

## 2. Creating Scheduled Agents for Repetitive Work

For tasks that should run on a timetable (e.g., keyword research, ad performance checks, content generation), create a Hermes agent with a cron schedule.

### Steps
1. **Define goal, context, and prompt**.
   - Goal: short description.
   - Context: files, data, or notes the agent needs (e.g., product catalog, keyword list).
   - Prompt: detailed instructions, preferably requesting a structured output (JSON) if the result will be consumed by another step.
2. **Create the agent**:
   ```
   hermes agent create <agent-name> \
     --goal "<short goal>" \
     --context "<context>" \
     --prompt "<detailed instructions>" \
     --schedule "<cron-expression>" \
     --on-success "<hermes kanban move <card-id> <column>>"
   ```
   - `--schedule` follows standard cron syntax (e.g., `0 9 * * *` for 09:00 daily).
   - `--on-success` is optional; use it to automatically move a Kanban card when the agent finishes successfully.
3. **Run manually** (if you don’t want a schedule):
   ```
   hermes agent run <agent-name>
   ```
4. **Inspect logs** for debugging:
   ```
   tail -f ~/.hermes/logs/agent/<agent-name>.log
   ```

### Pitfalls
- **Vague prompts** lead to unpredictable outputs; always specify the exact format you expect (e.g., `"Output JSON: {\"keywords\":[{\"term\":\"...\",\"cpc\":0,…}]}"`).
- **Missing context** – If the agent needs files that aren’t in its working directory, specify absolute paths or use `--workdir`.
- **Overlapping schedules** – Ensure cron expressions don’t cause resource contention; stagger long‑running tasks.

## 3. Linking Agents to a Kanban Board

Use a Kanban board to visualize work items (e.g., “Create caption for AP‑1512HH”, “Review ad performance”). Each card can be moved by agents or manually.

### Steps
1. **Initialize a board** for a division or project:
   ```
   mkdir -p ~/.hermes/kanban
   cat > ~/.hermes/kanban/<division>.json <<'EOF'
   {
     "columns": ["Backlog","Ready","In Progress","Review","Done"],
     "cards": []
   }
   EOF
   ```
2. **Add cards** manually or via agent `--on-success`:
   - Manual: `hermes kanban create --title "Task title" --column Backlog --labels marketing`
   - Agent: set `--on-success` to `hermes kanban move <card-id> <target-column>` where `<card-id>` is the card representing this task.
3. **Move cards** based on progress:
   ```
   hermes kanban move <card-id> <column>
   ```
4. **Review** the board anytime:
   ```
   cat ~/.hermes/kanban/<division>.json
   ```
   or use `hermes kanban show`.

### Pitfalls
- **Non‑unique IDs** – If you generate card IDs yourself, use timestamps or UUIDs to avoid collisions.
- **Malformed JSON** – A stray comma or missing bracket will break Kanban commands; validate with `python -m json.tool` before editing manually.
- **Stale cards** – Periodically archive cards that have lingered too long in a column (use the Kanban‑Dispatcher bot or a cron job).

## 4. Watcher Agents for Service Health

To catch downtime of external APIs (MCP servers, webhook endpoints, ad platforms), run a lightweight agent on a frequent schedule that alerts you via WhatsApp when something fails.

### Steps
1. **Create a watcher agent**:
   ```
   hermes agent create watcher-<service> \
     --goal "Check health of <service>" \
     --context "Endpoint URL and expected response" \
     --prompt "Perform a GET/POST to the endpoint; if response code != 200 or body missing expected field, send a WhatsApp message to owner with details." \
     --schedule "*/5 * * * *"
   ```
2. **Test** the agent manually first to ensure the prompt works and the alert is formatted correctly.
3. **Monitor** the agent’s logs for false positives.

### Pitfalls
- **Secret leakage** – Never put API keys or tokens directly in the prompt; store them in Hermes config (`hermes config set`) or memory and reference via variables if supported, or use the `--secret` flag where the tool accepts it.
- **Alert fatigue** – Add throttling (e.g., only alert if failure persists for two consecutive checks) to avoid spamming your phone.

## 5. Putting It All Together – Example Flow for a New Order

1. **Sejoli** sends `order.completed` webhook to Hermes.
2. Hermes validates the HMAC signature, extracts `customer_phone`, `customer_name`, `product_name`, `order_id`.
3. The webhook subscription’s prompt runs:
   - Sends a WhatsApp message: "Halo {customer_name}, terima kasih telah membeli {product_name}."
   - Creates a Kanban card "Follow‑up WA – order #{{order_id}}" in column *To Do*.
4. A **follow‑up agent** (scheduled or triggered by the card moving to *In Progress*) sends a second message after 2 days asking for feedback or offering a complementary product.
5. An **analytics watcher** runs every 30 minutes, checks Meta Ads CPC/ROI, and sends a WhatsApp alert if CPC rises >20 % or ROI <1.5.
6. A **content‑edu agent** runs each morning to generate an educational infographic and caption, which you can broadcast via WhatsApp blast.

By combining webhook‑triggered actions, scheduled agents, Kanban tracking, and watcher bots, a single operator can run a fully automated marketing and sales pipeline with minimal manual intervention.