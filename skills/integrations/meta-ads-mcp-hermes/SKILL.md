---
name: meta-ads-mcp-hermes
description: "Fix Meta Ads MCP in Hermes (OAuth + _meta 400)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, meta-ads, oauth, facebook, troubleshooting]
    related_skills: [hermes-agent, make-mcp-oauth-setup-in-hermes]
---

# Meta Ads MCP in Hermes

Connect Hermes to Meta's hosted Ads MCP server (`https://mcp.facebook.com/ads`) and fix the two
things that stop it working out of the box: Meta refuses dynamic client registration, and the
`mcp` Python SDK sends an empty `_meta` object that Meta rejects with HTTP 400.

## When to use

- Adding Meta Ads (Facebook/Instagram) tooling to Hermes.
- `hermes mcp test <name>` returns `HTTP 400 from POST https://mcp.facebook.com/ads`.
- Any **Meta-hosted** MCP server (ads, devtools, WhatsApp Business) fails to connect with a 400.
- Re-applying the `_meta` patch after `hermes update`.

## Symptom → cause map

| Symptom | Cause |
|---|---|
| `Dynamic registration is not available for this client` | Meta only allows DCR for validated clients (Claude, ChatGPT, Codex, Cursor). Must use your own Meta app as a static OAuth client. |
| `HTTP 400 from POST .../ads` on every request, curl with the same token returns 200 | mcp SDK ≥ 2.0 writes `"_meta": {}` into JSON-RPC params. Meta answers `-32602 "meta" for Request must be an dict or null.` |
| `401 Authentication Required` | No token, or the token expired (user tokens live ~1-2h unless exchanged; the OAuth flow mints a ~60-day one). |
| `OAuthNonInteractiveError: MCP OAuth requires browser authorization but no interactive session is available` | The gateway runs headless (systemd/cron) and cannot open a browser. Mint the tokens once with `hermes mcp login <name>` in a **PTY** (`ssh -t`), then restart the gateway — it only needs the tokens the flow writes. |
| `configured OAuth client changed (client_id 'X' -> 'X')` and a re-auth loop on every restart | `oauth.client_secret` in `config.yaml` differs from `client_secret` in `~/.hermes/mcp-tokens/<name>.client.json`. Hermes **deletes the tokens on every start** when they disagree (the client_id looks unchanged, so the log is misleading). Align the two and the loop stops. |
| Works on the laptop, HTTP 400 on a headless VPS/Linux box | The server install keeps its venv **outside** `HERMES_HOME` (`/usr/local/lib/hermes-agent/venv`), so the `_meta` patch is missing there. `targets()` must also glob `sys.prefix` / `/usr/local/lib/hermes-agent`. |

## Setup

### 1. Create a Meta app for the connector

developers.facebook.com → create app (type: Business) → add **Facebook Login**. Note App ID +
App Secret. Publishing the app is not required for the account owner to authorize it.

### 2. Point Hermes at Meta's server using YOUR app as the OAuth client

Discovery for `https://mcp.facebook.com/ads` advertises a `registration_endpoint`, but Meta
rejects Hermes' DCR. Supplying `oauth.client_id`/`client_secret` makes Hermes **pre-register** and
skip DCR entirely (see `tools/mcp_oauth.py::_maybe_preregister_client`).

```yaml
mcp_servers:
  meta-ads:
    url: https://mcp.facebook.com/ads
    type: http
    enabled: true
    auth: oauth
    protocol: legacy          # Meta is a handshake-era server; skip the server/discover probe
    oauth:
      client_id: "2176994976587862"          # QUOTE IT — the app id is numeric and config set stores it as an int,
                                             # which fails pydantic's OAuthClientInformationFull (str required)
      client_secret: "<app secret>"
      scope: "ads_management ads_read business_management pages_show_list pages_manage_ads pages_read_engagement"
      redirect_host: localhost                # literal 127.0.0.1 is fine too; Meta accepts http://localhost:<port>/callback
      redirect_port: 8765                     # pin it so the registered redirect URI never changes
```

Set the keys with `hermes config set mcp_servers.meta-ads.oauth.<key> <value>`; for `client_id`
follow with the quoting fix in Paths & quirks below.

### 3. Authorize (interactive — needs a browser)

```bash
hermes mcp login meta-ads
```

It prints a `facebook.com/dialog/oauth` URL, opens the browser, and catches the loopback callback
itself. Approve; tokens land in `~/.hermes/mcp-tokens/<name>.json` with a ~60-day expiry and a
refresh token, so Hermes re-auths silently afterwards.

### 4. Patch the SDK's empty `_meta` (the real blocker)

```bash
python ~/.hermes/skills/integrations/meta-ads-mcp-hermes/scripts/patch_mcp_empty_meta.py
```

Idempotent; finds **every** `mcp/shared/jsonrpc_dispatcher.py` under the Hermes home and turns

```python
out_params["_meta"] = out_meta        # -> {}
```

into

```python
if out_meta:
    out_params["_meta"] = out_meta
```

A non-empty `_meta` (progressToken etc.) is unchanged, so no other server is affected. Backups are
written next to each patched file as `*.py.bak-empty-meta`.

### 5. Verify

```bash
hermes mcp test meta-ads     # expect: Connected + "Tools discovered: 98"
```

Then exercise a real call (a `/tmp` script against the endpoint, or just ask in a new session):
`ads_get_ad_accounts` is the cheap smoke test. A tool call returns
`is_ads_mcp_enabled: true/false` per ad account — Meta rolls Ads MCP out gradually, so an account
with `false` will answer with `is_ads_mcp_disabled_reason` instead of data. That is Meta-side, not a
setup fault.

### 6. Restart to see the tools

MCP tools are injected at session start. Restart the CLI / start a new session, and restart the
gateway (`hermes gateway restart`) if the bots need them.

## Paths & quirks

- **`hermes config set` turns numeric values into YAML ints.** `client_id: 2176994976587862`
  (unquoted) makes the OAuth flow die with `Input should be a valid string [type=string_type,
  input_type=int]`. The `patch`/`write_file` tools refuse to touch `config.yaml` by design, so fix
  the quoting directly (Hermes' own error message says to) and re-run `hermes mcp login`.
- **Hermes imports `mcp` from more than one environment.** On a Windows install there were three
  copies: `hermes-agent/venv`, `installs/<id>/environments/<id>/venv`, and `cache/uv/archive-*`.
  The one the MCP client actually loads is **not necessarily** `hermes-agent/venv` — patch all of
  them (`patch_mcp_empty_meta.py` does) or you will "fix" it and still see the 400.
- **`hermes mcp add` is discovery-first.** Against an OAuth-protected server it fails to connect and
  prompts `Save config anyway? [y/N]` — pipe `printf 'y\ny\n'` to accept it non-interactively, then
  fill in `auth`/`oauth` afterwards.
- **Diagnosing a stubborn 400:** dump the SDK's wire traffic instead of guessing. Either call
  `mcp.client.streamable_http.streamable_http_client(url, http_client=<client with a wrapped
  .send>)` from the venv python (mcp 2.0.0 renamed `streamablehttp_client` → `streamable_http_client`
  and moved `headers=` into `create_mcp_http_client`), or read the returned JSON-RPC error — Meta
  puts the reason in an SSE `data:` line, which is why Hermes' own error text often shows no body.
- **Re-apply after `hermes update`.** The patch lives in site-packages. If Meta tools start 400ing
  again, re-run the patch script.
- **Secrets hygiene.** The app secret ends up in `config.yaml` and the token in `mcp-tokens/`. Never
  paste either into a chat transcript; rotate the secret at developers.facebook.com → Settings →
  Basic if it leaks, then re-run `hermes mcp login meta-ads`.

## Querying campaigns & performance (pattern proven 2026-10)

Use `ads_get_ad_entities` as the metrics source — `ads_insights_*` tools are trend/anomaly only and take no date range.

### Smoke test then query

1. `ads_get_ad_accounts` (with a 20-char `client_conversation_id` — same value for the whole conversation) and check `is_ads_mcp_enabled` + `is_queryable` per account. If `false`, surface `is_ads_mcp_disabled_reason` and stop — that account is still in Meta's gradual rollout, not a config error.
2. `ads_get_ad_entities` at `level=campaign` (or `adset`/`ad`). Required: `ad_account_id`, `client_conversation_id`, `advertiser_request` verbatim from the user. Reuse the same `client_conversation_id` across the conversation.

### Fields that work for spend / sales / ROAS

```
fields: [id, name, amount_spent, omni_purchase, omni_purchase_values, cost_per_omni_purchase, purchase_roas, impressions, clicks]
```

- `amount_spent.value` = spend (string, unit IDR).
- `omni_purchase` = sales count (string integer).
- `omni_purchase_values.value` = omzet / conversion value (what ROAS is computed from). Request it explicitly — `purchase_roas` alone does not return the numerator.
- `cost_per_omni_purchase.value` = CPP. Do not use `cost_per_result` at campaign level without `ads_get_field_context`.

### Filtering & time slicing

- Filter by name: `filtering: [{"field":"name","operator":"CONTAIN","value":["Sales - Affiliate Air Minum"]}]` — verify filterable via `ads_get_field_context` before adding new fields.
- Today: `date_preset: "today"`.
- Range with daily rows: `time_range: '{"since":"YYYY-MM-DD","until":"YYYY-MM-DD"}'` + `time_increment: "1"` — without `time_increment` you get a single aggregated row.
- Omit `time_range`/`date_preset` defaults to last 28 days aggregated.

### Raw-data requests

When the user says "tampilkan data mentahnya", return the MCP JSON verbatim (ad_accounts / ad_entities) and then add a short human table underneath — do not summarize away the raw payload.

### Pitfalls

- Never `curl https://mcp.facebook.com/ads` to prove connectivity — it returns 401/404 by design; only the MCP OAuth flow works. Use the MCP tool as the probe.
- Do not mix `date_preset` and `time_range` in one call.
- `is_ads_mcp_enabled:false` is Meta-side rollout gating — no local fix; check the other account under the same Business Manager (e.g. Smart Millionaire 1497110470872963 was enabled while Lee Juan 1329252664335404 was not).
- Always verify account timezone first with `level=ad_account` field `timezone_name` before interpreting "hari ini" — Smart Millionaire is `Asia/Jakarta`; answer dates/times in WIB, state the date explicitly (e.g. "5 Okt 2026 WIB"), and resolve "today" via `TZ='Asia/Jakarta' date +%Y-%m-%d` on every call — never assume UTC or server UTC.
- Prefer explicit `time_range: '{"since":"YYYY-MM-DD","until":"YYYY-MM-DD"}'` in Asia/Jakarta when the user says "hari ini" or "dr tgl 1" — `date_preset:today` follows account timezone but is not auditable in logs; explicit range prevents UTC vs WIB confusion. For cron report jobs, compute the date inside the job with `TZ='Asia/Jakarta' date +%Y-%m-%d` on every tick — do not hardcode the date at creation time.
- Cron `schedule` on this gateway is evaluated in gateway local time (WIB, `+07:00`) — `0 18 * * *` means 18:00 WIB directly; do not apply an extra UTC→WIB offset (11 UTC = 18 WIB is wrong here).
- Treat `omni_purchase:null` with `amount_spent>0` as attribution delay, not zero sales — Meta purchase events lag 30-60 min intraday; report as "belum ke-track / delay" and re-query later instead of claiming 0 sales.
- At adset level `campaign_name` is not filterable — fetch all adsets for the date and filter client-side by `campaign_id`, or filter at `level=campaign` with `name CONTAIN`; do not pass `campaign_name` in `filtering`.
- High CTR (8-20%) with 0 `omni_purchase` signals clickbait creative, not success — always evaluate `CVR = omni_purchase / clicks` and `CPP` alongside CTR/CPM before recommending scale.

## Useful references

- Meta's own docs: https://developers.facebook.com/documentation/mcp
- Hermes MCP guide: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/
