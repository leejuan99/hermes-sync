# Provider OAuth quirks (Hermes MCP client)

Per-provider notes for `mcp_servers.<name>.oauth`. Extend this file rather than
creating a new one per provider.

## Pre-registered client (works for any DCR-refusing provider)

When the provider advertises a `registration_endpoint` but refuses Hermes'
registration, stop trying to make DCR work and hand Hermes a client identity the
provider already knows:

```yaml
mcp_servers:
  <name>:
    type: http
    url: <endpoint>
    enabled: true
    auth: oauth
    oauth:
      client_id: "<provider app/client id>"   # MUST be a quoted string, never bare digits
      client_secret: "<provider secret>"
      scope: "scope-one scope-two"
      redirect_host: localhost
      redirect_port: 8765
```

Setting `oauth.client_id` makes Hermes persist that identity and skip RFC 7591 DCR
entirely. `token_endpoint_auth_method` is derived automatically
(`client_secret_post` when a secret is present, `none` otherwise). Because the stored
client is bound to its registered redirect URI, changing `redirect_port` later means
deleting `~/.hermes/mcp-tokens/<name>.client.json` and re-running the login.

Accepted `oauth.*` keys: `client_id`, `client_secret`, `scope`, `redirect_port`,
`redirect_uri`, `redirect_host`, `client_name`, `client_metadata_url`, `cimd`,
`user_agent`, `timeout`.

## Meta (Facebook) — Ads MCP

- Endpoint `https://mcp.facebook.com/ads`. Discovery:
  `https://mcp.facebook.com/.well-known/oauth-protected-resource/ads` → issuer
  `https://www.facebook.com/ads`; authorize at `https://www.facebook.com/v26.0/dialog/oauth`,
  token at `https://graph.facebook.com/v26.0/oauth/access_token`.
- **DCR is refused.** Registering with Hermes' own client metadata returns
  `400 invalid_client_metadata: "Dynamic registration is not available for this client."`
  Meta only registers its own named AI clients. Use the user's own Meta developer app
  as the pre-registered client: App ID → `client_id`, App secret → `client_secret`.
- **No redirect-URI allowlisting step.** Meta accepts arbitrary
  `http://localhost:<port>/callback` URIs for such an app — the authorize endpoint
  redirects straight to the login page rather than returning `URL blocked`.
- **A hand-written `scope:` is ignored.** Hermes requests the server's advertised
  `scopes_supported` (`ads_management ads_read catalog_management business_management
  pages_show_list pages_manage_ads instagram_basic ads_mcp_management`). A user token
  granted a subset still authenticates.
- Tokens come back long-lived (`expires_in` ≈ 5.18M s ≈ 60 days) with a refresh grant.
- Validate the user's own token with the Graph API rather than guessing:
  `curl "https://graph.facebook.com/v21.0/debug_token?input_token=<tok>&access_token=<app_id>|<app_secret>"`
  → `is_valid`, `expires_at`, `scopes`.

## Figma

Figma allowlists DCR by exact `client_name` (`Claude Code` registers, others 403), so
Hermes sets `client_name: "Claude Code"` and `scope: "mcp:connect"` automatically for
`mcp.figma.com`. Overriding `oauth.client_name` re-breaks it — only do so to match a
name Figma actually allows.
