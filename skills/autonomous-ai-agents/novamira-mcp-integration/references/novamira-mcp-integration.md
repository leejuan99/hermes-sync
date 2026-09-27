# Novamira MCP Integration — Detailed Reference

Extended reference for connecting WordPress (Novamira plugin) to Hermes via MCP.

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

## Authentication

Use **Application Passwords** (WordPress → Users → Profile → Application Passwords):
- Username: WP username
- Password: Generated app password (NOT login password)

## Sandbox Pollution Issue (CRITICAL)

**Problem**: PHP files in `wp-content/novamira-sandbox/` are **auto-loaded on every WordPress request**. A test file like `test_write.php` that outputs directly (`echo`, `print`) will pollute the JSON-RPC stream, breaking **all MCP communication**.

**Symptoms**:
- "Unexpected token 'e', 'test write...' is not valid JSON"
- "Invalid Request: jsonrpc version must be '2.0'"
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

## Error Handling Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `parameters is a required property of input` | Missing `parameters` wrapper | Wrap args in `parameters: { ... }` |
| `Connection closed` / `Failed to connect` | Credentials, URL, network | Check WP API URL, credentials, firewall |
| `402 credits` | OpenRouter credits exhausted | Switch provider or add credits |
| `test write success... not valid JSON` | Sandbox pollution | Delete/disable the offending PHP file in sandbox |

## SEO GEO/AIO Rewrite Template

Structure for AI-overview-friendly content:
1. **Executive Summary** (TL;DR for AI snippets)
2. **Structured H2/H3 sections**
3. **Key Points** as bullet list
4. **FAQ section** (H3 questions + paragraph answers) — enables FAQ Schema
5. **Key Takeaways** list
6. **Disclaimer** about auto-generation

## Testing Connection

```bash
hermes mcp test novamira-smartmillionaire
# Should show: "Connected" + "Tools discovered: X"
```

## Fluent CRM Automation Structure

Triggers: `fluent_crm/contact_created`, `fluentform_submission_inserted`, `fluentcrm_contact_added_to_lists`

Steps (in `sequences` array):
- `action` types: `send_custom_email`, `fluentcrm_wait_times`, `add_to_email_sequence`, `funnel_condition`
- `conditional` type: `funnel_condition` with `conditions` array for branching
- Delays in seconds (e.g., 259200 = 3 days)

---

*Generated from session: WordPress + Novamira MCP integration with Fluent CRM contact cleanup (8 suspicious contacts deleted, 55 added to Review list), RSS-to-draft workflow attempted.*