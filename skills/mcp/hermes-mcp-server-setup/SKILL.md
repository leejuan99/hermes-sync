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
- **`405`/`404`** — probably not a streamable-HTTP endpoint, or the path is wrong.

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
- **The provider still has to allowlist the redirect URI.** Hermes defaults to
  `http://<redirect_host or 127.0.0.1>:<port>/callback`; pin it with
  `oauth.redirect_host` / `oauth.redirect_port`. Check it *before* starting a browser
  flow: hit the provider's `authorization_endpoint` with that `redirect_uri` and look
  for `URL blocked` / `redirect_uri is not whitelisted` instead of the login page.
- **Never build on a pasted token without validating it.** They are usually already
  expired. Meta's Graph `debug_token`
  (`?input_token=<tok>&access_token=<app_id>|<app_secret>`) returns `is_valid`,
  `expires_at` and the granted `scopes` in one call.
- **An OAuth server left `enabled: true` without a completed login errors on every
  startup.** If you abandon a flow (`skip`, or you kill the process), set
  `enabled: false` again or finish the login.

## Files

- `scripts/probe_mcp_endpoint.sh` — dead-endpoint vs OAuth-discovery probe (step 1).
- `references/oauth-provider-quirks.md` — pre-registered-client config block plus
  per-provider OAuth notes. Extend that file instead of adding a new one per provider.
