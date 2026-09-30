---
name: hermes-mcp-server-setup
description: "Use when adding or debugging an MCP server in Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, mcp, oauth, integration, configuration]
    related_skills: [hermes-agent]
---

# Adding an MCP server to Hermes

For any external MCP server (remote HTTP or local stdio) that should show up as
`mcp_<server>_<tool>` tools. The bundled `hermes-agent` skill's
`references/native-mcp.md` documents the config *shape* and the stdio env filter;
this skill is the *procedure*, the auth decision, and the failure modes.

## Procedure

### 1. Probe the endpoint before configuring anything

Run `scripts/probe_mcp_endpoint.sh <url>`. It sends `initialize`, prints the
`WWW-Authenticate` challenge, and walks the OAuth discovery chain. What you look for:

- **`200` + `serverInfo`** — live MCP server, no auth.
- **`401` + `WWW-Authenticate: Bearer ... resource_metadata="..."`** — OAuth, and the
  header names the discovery document. Fetch it, then the authorization-server
  metadata: you need `authorization_endpoint`, `token_endpoint`, `scopes_supported`,
  and whether `registration_endpoint` exists (that decides step 3).
- **`405`, typically with `Allow: POST`** — the endpoint is *alive*. MCP is POST-only JSON-RPC, so a
  `GET` is rejected (`MCP endpoints accept POST for JSON-RPC; GET is not supported`). Re-probe with a
  POST before concluding anything: treating a GET's 405 as "the server is down" starts a hunt for an
  outage that is not happening. `scripts/probe_mcp_endpoint.sh` already sends `initialize` over POST.
- **`404`** — the path really is wrong, or this host serves MCP elsewhere.

### 2. Add the server

```bash
hermes mcp add <name> --url <url>                  # HTTP
hermes mcp add <name> --command <bin> --args ...  # stdio (args must come last)
```

Discovery is connection-first. When the first connect fails it asks
`Save config anyway? [y/N]` — in a non-interactive shell that prompt reads EOF and
**nothing is saved**. Pipe the answers: `printf 'y\ny\n' | hermes mcp add ...`.
The entry lands `enabled: false`; enable it explicitly.

### 3. Choose the auth mode, in this order

1. **`oauth` with dynamic client registration** — works when the provider exposes a
   `registration_endpoint` *and* accepts Hermes' client metadata.
2. **`oauth` with a pre-registered client** — required when the provider refuses DCR
   (common for first-party platforms that only register named AI clients). Set
   `mcp_servers.<name>.oauth.client_id` (plus `client_secret` for a confidential app)
   and Hermes persists that identity and skips registration entirely. Exact config
   block and per-provider notes: `references/oauth-provider-quirks.md`.
3. **`headers.Authorization: "Bearer ..."`** — static token, no browser flow. Use when
   the provider hands you a long-lived token and refuses to register Hermes at all.

### 4. Enable, log in, test

```bash
hermes config set mcp_servers.<name>.enabled true
hermes mcp login <name>       # OAuth only: prints the URL, opens the browser, listens on a localhost callback
hermes mcp test <name>
hermes mcp configure <name>   # optionally restrict which discovered tools are exposed
```

`hermes mcp login` is interactive: run it in a real terminal (background + `pty=true`
works) and it will also accept a pasted redirect URL if the callback never fires.

### 5. Verify with the stored credential, not the flow's exit code

Tokens land in `~/.hermes/mcp-tokens/<name>.json`, next to `<name>.client.json`
(client identity) and `<name>.meta.json` (discovered metadata). Pull the
`access_token` out and hit the endpoint with plain curl. A `200` carrying the
server's `serverInfo` proves the credential works — anything else is a credential
problem, not a config problem. Do this before telling the user it is set up.

## Pitfalls

- **`hermes config set` writes numeric-looking values as YAML ints.**
  `oauth.client_id: 2176994976587862` parses as `int` and the OAuth client model
  rejects it (`Input should be a valid string`). Passing `'"217..."'` does not help —
  the quotes get stored literally. Set the value by editing `config.yaml` directly;
  the agent's `patch`/`write_file` tools refuse that file by design and Hermes' own
  refusal message says to edit it directly. Do that with an explicit script rather
  than a shell one-liner that hides the change.
- **A `400` from the endpoint is not automatically an auth failure.** If
  `hermes mcp test` fails but a raw curl with the same stored token returns `200`,
  the credentials are fine and the difference is in Hermes' transport request
  (headers, `Accept`, protocol version). Compare the two requests before changing any
  auth config.
- **A tool call that returns data is the only proof of health.** When someone reports an MCP server is
  "not working", find out whether a real tool call ever returned rows. If it did, the transport, auth
  and any SDK patch are all fine and the fault is in the interpretation of the result — do not reopen
  the setup. Probe the tool, not the URL.
- **The provider still has to allowlist the redirect URI, and a passing probe does not
  prove it is allowlisted.** Hermes defaults to
  `http://<redirect_host or 127.0.0.1>:<port>/callback`; pin it with
  `oauth.redirect_host` / `oauth.redirect_port`. Pre-probing the provider's
  `authorization_endpoint` with that `redirect_uri` catches a flat `URL blocked`
  refusal, but not the common case: providers that serve the login page on the GET and
  validate the redirect only at *approval* time, after the user has consented. App
  state flips this — an unpublished Meta app accepts the loopback URI, and publishing
  it starts rejecting the same URI. So when the flow dies with `This redirect failed
  because the redirect URI is not whitelisted in the app's Client OAuth Settings`,
  the fix is in the provider's dashboard (turn Client + Web OAuth Login on, add the
  exact URI) and there is nothing to change in Hermes' config — have the user fix it
  and re-run the login.
- **The loopback callback window is 5 minutes by default and is the usual cause of a
  "silent" failed login.** `hermes mcp login` waits `oauth.timeout` seconds (default
  `300`) for the callback, while the user has to read your message, switch windows and
  click through consent. Raise it *before* starting the flow
  (`hermes config set mcp_servers.<name>.oauth.timeout 900`) and paste the printed
  authorization URL into your reply so a slow browser launch does not burn the whole
  attempt. Diagnosing a timeout: a provider-side rejection never reaches the loopback
  port, so it leaves **no** line in `logs/errors.log` and looks identical to the user
  simply not getting there — check whether anything ever hit the callback port before
  blaming the redirect URI.
- **Never build on a pasted token without validating it.** They are usually already
  expired. Meta's Graph `debug_token`
  (`?input_token=<tok>&access_token=<app_id>|<app_secret>`) returns `is_valid`,
  `expires_at` and the granted `scopes` in one call.
- **An OAuth server left `enabled: true` without a completed login errors on every
  startup.** If you abandon a flow (`skip`, or you kill the process), set
  `enabled: false` again or finish the login.
- **A headless gateway can never complete an OAuth login.** `hermes mcp login` needs a
  browser and a loopback callback, so from cron/systemd it dies with
  `OAuthNonInteractiveError: MCP OAuth requires browser authorization but no
  interactive session is available`. Mint the tokens once from a PTY (`ssh -t ...`), or
  copy `mcp-tokens/` from a machine that already authorized — the gateway only ever
  reads those files, so it starts working the moment they exist.
- **`configured OAuth client changed (client_id 'X' -> 'X')` means the *secret* changed,
  not the id.** Hermes **deletes the stored tokens on every start** when
  `oauth.client_secret` in `config.yaml` disagrees with `client_secret` in
  `<name>.client.json`, so the server re-auth-loops on each restart. The message names
  only the client_id, which makes it read as a no-op. Align the two values and the loop
  stops.
- **The SDK itself sometimes needs patching, and that patch is per-machine.** When a
  hosted server rejects an otherwise-valid request — the textbook case is an empty
  `_meta` object answered with JSON-RPC `-32602` — the fix lands in
  `site-packages/mcp/...`, which no config sync carries. Patch **every** venv Hermes
  imports `mcp` from; on a server install one of them is
  `/usr/local/lib/hermes-agent/venv`, outside `~/.hermes`, so a script that globs only
  the Hermes home reports "nothing to do" while the server keeps failing. Re-apply it
  after upgrades, and see `hermes-multimachine-sync` when two hosts must stay in step.

## Files

- `scripts/probe_mcp_endpoint.sh` — dead-endpoint vs OAuth-discovery probe (step 1).
- `references/oauth-provider-quirks.md` — pre-registered-client config block plus
  per-provider OAuth notes. Extend that file instead of adding a new one per provider.
- `references/direct-tool-calls.md` — authenticated `tools/call` over curl (how to pull
  real data after a login succeeds) plus the Meta Ads read-call notes.
