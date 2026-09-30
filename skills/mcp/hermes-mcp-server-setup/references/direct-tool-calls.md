# Calling MCP tools directly over curl

Once a remote MCP server connects, this is the fastest way to check real data and to
diagnose a tool-level failure with Hermes' transport out of the picture. `initialize`
and `tools/list` are the same request with a different `method`.

## The request

```bash
TOKEN=$(python -c "import json,sys;print(json.load(open(sys.argv[1]))['access_token'])" \
  "$HOME/.hermes/mcp-tokens/<name>.json")

curl -s -X POST "$URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  --data-binary '{"jsonrpc":"2.0","id":1,"method":"tools/call",
                  "params":{"name":"<tool>","arguments":{}}}'
```

Rules that cost time when ignored:

- **`Accept` must include `text/event-stream`.** The streamable-HTTP transport answers
  in SSE frames; accepting only `application/json` gets a `406` or an empty body.
- **Parse the `data: ` frames, not the whole body.** Everything else in the response is
  SSE framing (`event:`, blank separators), so `json.loads(body)` fails on a valid
  reply. Collect the lines starting with `data: ` and join them.
- **Read the tool's `inputSchema` from `tools/list` first.** A missing required argument
  comes back as `-32602` / `isError`, which reads like a permission or auth problem.
- **Check `isError` and `structuredContent`, not just the HTTP status.** A tool that ran
  and refused still returns `200` with `isError: true`.

## Provider notes: Meta Ads (`https://mcp.facebook.com/ads`)

- Every call needs `client_conversation_id` (any stable unique string) and a free-text
  `advertiser_request` describing what the user asked; omitting them fails validation.
- Reading is one generic entity tool, `ads_get_ad_entities`, not a family of per-level
  readers: pass `ad_account_id`, `level: campaign | adset | ad`, and optionally
  `fields`. It is paginated — follow up when it reports more.
- **`date_preset` does not filter entity metrics.** The same `amount_spent` comes back
  with and without a 30-day preset, so those figures are lifetime per entity. Label them
  as lifetime; never present them as a period total.
- **Metrics arrive as `{value, unit}` objects and are already in the account currency.**
  `{"value": "5289755", "unit": "IDR"}` is Rp 5,289,755 — do not divide by 100 or
  "convert", even though sibling fields elsewhere are named `*_cents`. Percentages are
  comma-decimal strings (`"ctr": "10,78%"`).
- `ads_get_ad_accounts` is the fastest capability check: per account it reports whether
  that account is enrolled in the Ads MCP rollout.
- `ads_insights_performance_trend` returned an empty result with placeholder
  `conversation_intent` / `conversation_topic` values. When period-accurate numbers are
  what the user wants, source them from the entity tool's own metrics rather than
  assuming the trend tool is broken and reopening the setup.
