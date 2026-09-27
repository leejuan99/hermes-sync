---
name: novamira-mcp-integration
description: "Configure and use Novamira WordPress plugin via MCP with Hermes Agent"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [novamira, wordpress, mcp, fluent-crm, gutenberg, rss-automation]
---

# Novamira MCP Integration

**Trigger**: Working with WordPress sites that have the Novamira plugin installed, needing to connect to Hermes via MCP for automation (Fluent CRM, Gutenberg, file ops, WP-CLI).

**Scope**: Configuration, common abilities, patterns, and pitfalls for Novamira ↔ Hermes MCP integration.

---

## MCP Server Configuration

Add to `~/.hermes/config.yaml` under `mcp_servers`:

```yaml
mcp_servers:
  novamira-smartmillionaire:
    command: npx
    args: ["-y", "@automattic/mcp-wordpress-remote@latest"]
    env:
      WP_API_URL: "https://your-site.com/wp-json/mcp/novamira"
      WP_API_USERNAME: "your-username"
      WP_API_PASSWORD: "your-app-password"
    enabled: true
```

**Critical**: Use `args: ["-y", "@automattic/mcp-wordpress-remote@latest"]` (array of strings), NOT a single string.

---

## Key Abilities

### Fluent CRM
| Ability | Description |
|---------|-------------|
| `fluent-crm/list-contacts` | List/filter contacts with tags, lists, status |
| `fluent-crm/get-contact` | Full contact profile by ID or email |
| `fluent-crm/delete-contact` | Hard delete (use `delete_emails: true` to purge email log) |
| `fluent-crm/manage-list` | Create/update/delete/merge lists |
| `fluent-crm/apply-segments-to-contacts` | Bulk add/remove tags & lists |
| `fluent-crm/list-automations` | List funnels with subscriber counts |
| `fluent-crm/get-automation` | Funnel details with sequences (`include_bodies: true` for email content) |
| `fluent-crm/upsert-contact` | Create/update contact |
| `fluent-crm/send-email-to-contact` | One-off email via FluentSMTP |

### Gutenberg Content
| Ability | Description |
|---------|-------------|
| `novamira/gutenberg-write-content` | Write dynamic blocks directly |
| `novamira/gutenberg-add-pending-change` | Queue static/native block changes |
| `novamira/gutenberg-enable-batch-finalization` | Finalize queued changes (requires Block Editor Queue page open) |
| `novamira/gutenberg-get-finalizer-runtime` | Check if Block Editor Queue page is open |

### File System & PHP Execution
| Ability | Description |
|---------|-------------|
| `novamira/execute-php` | Run arbitrary PHP in WP context (full $wpdb, functions, plugins) |
| `novamira/write-file` | Write to sandbox (`wp-content/novamira-sandbox/`) or anywhere under ABSPATH (non-PHP) |
| `novamira/read-file` | Read files |
| `novamira/delete-file` | Delete files |
| `novamira/disable-file` | Disable sandbox file (appends `.disabled`) |
| `novamira/list-directory` | List files with glob patterns |

### WP-CLI
| Ability | Description |
|---------|-------------|
| `novamira/run-wp-cli` | Run WP-CLI commands (sync or async) |
| `novamira/get-wp-cli-job` | Check async job status |

---

## Common Patterns

### Bulk Contact Operations (Add to List)
```json
{
  "ability_name": "fluent-crm/apply-segments-to-contacts",
  "arguments": {
    "add_lists": [13],
    "contact_ids": [2238, 2257, 2261, ...]
  }
}
```

### Fetch RSS → Create Draft Post (via execute-php)
```php
$rss = simplexml_load_string(@file_get_contents($feed_url));
foreach ($rss->xpath('//item') as $item) {
  $title = (string)$item->title;
  $content = (string)$item->children('content', true)->encoded;
  // Clean, rewrite for SEO GEO/AIO, create draft via wp_insert_post
}
```

### Delete Contact
```json
{
  "ability_name": "fluent-crm/delete-contact",
  "arguments": {
    "contact_id": 2234,
    "delete_emails": true
  }
}
```

---

## Authentication

Use **Application Passwords** (WordPress → Users → Profile → Application Passwords):
- Username: WP username
- Password: Generated app password (NOT login password)

---

## Sandbox Pollution Issue (CRITICAL)

**Problem**: PHP files in `wp-content/novamira-sandbox/` are **auto-loaded on every WordPress request**. A test file like `test_write.php` that outputs directly (`echo`, `print`) will pollute the JSON-RPC stream, breaking **all MCP communication**.

**Symptoms**:
- "Unexpected token 'e', 'test write...' is not valid JSON"
- "Invalid Request: jsonrpc version must be '2.0.0'"
- Transport fails during initialization
- Connection closed errors

**Fix**: Delete or disable the polluting file:
```php
// Via execute-php (cleanest - no output)
unlink('/www/wwwroot/your-site.com/wp-content/novamira-sandbox/test_write.php');

// Or via abilities:
novamira/disable-file   // appends .disabled
novamira/delete-file    // removes file
```

**Prevention**: Never write PHP files that output directly (`echo`, `print`, `var_dump`) to the sandbox. Only write files meant to be `require_once`d.

---

## Error Handling Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `parameters is a required property of input` | Missing `parameters` wrapper | Wrap args in `parameters: { ... }` |
| `Connection closed` / `Failed to connect` | Credentials, URL, network | Check WP API URL, credentials, firewall |
| `402 credits` | OpenRouter credits exhausted | Switch provider or add credits |
| `test write success... not valid JSON` | Sandbox pollution | Delete/disable the offending PHP file in sandbox |

---

## SEO GEO/AIO Rewrite Template

Structure for AI-overview-friendly content:
1. **Executive Summary** (TL;DR for AI snippets)
2. **Structured H2/H3 sections**
3. **Key Points** as bullet list
4. **FAQ section** (H3 questions + paragraph answers) — enables FAQ Schema
5. **Key Takeaways** list
6. **Disclaimer** about auto-generation

---

## Testing Connection

```bash
hermes mcp test novamira-smartmillionaire
# Should show: "Connected" + "Tools discovered: X```
```

## Troubleshooting stdio wrapper

If `hermes mcp test` shows connected but 0 tools, while direct HTTP calls to the MCP endpoint succeed, the stdio wrapper (`npx -y @automattic/mcp-wordpress-remote@latest`) may not be forwarding required headers (e.g., `Mcp-Session-Id`) or may be outputting stray data that corrupts the JSON‑RPC stream.

**Steps to diagnose:**
1. Run the wrapper manually in a terminal to see its raw output:
   ```bash
   npx -y @automattic/mcp-wordpress-remote@latest
   ```
   Leave it running, then in another terminal send a minimal JSON‑RPC request (e.g., `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}`) and observe the response.
2. Look for any extra output before the JSON (echo, warnings, PHP notices). Such output will break the RPC stream.
3. If you see stray output, check the WordPress sandbox (`wp-content/novamira-sandbox/`) for PHP files that `echo`/`print`. Remove or disable them (see the “Sandbox Pollution Issue” section).
4. If the wrapper works fine manually but fails via Hermes, verify that Hermes is using the correct environment variables (WP_API_URL, WP_API_USERNAME, WP_API_PASSWORD) and that no extra whitespace is injected into the args.

**Work‑arounds:**
- If your Hermes version supports MCP over HTTP, add the server via `--url` instead of `--command`/`--args`:
  ```bash
  hermes mcp add novamira-leejuan-com --url https://leejuan.com/wp-json/mcp/novamira --auth basic --username leejuan --password <APP_PASS>
  ```
- Otherwise, fix the sandbox pollution or use a custom wrapper that strips non‑JSON output.

After fixing, re‑run `hermes mcp test <name>`; you should see the correct number of tools discovered.

---

## Related Files

- `references/novamira-mcp-integration.md` — Full detailed reference
- `templates/rss-workflow.php` — Starter PHP for RSS→draft workflow

*Generated from session: WordPress + Novamira MCP integration with Fluent CRM contact cleanup (8 suspicious contacts deleted, 55 added to Review list), RSS-to-draft workflow attempted.*