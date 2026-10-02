---
name: wordpress-mcp-integration
description: "Integrate WordPress (via Novamira plugin) as MCP server in Hermes for Fluent CRM contact management, content automation, and site operations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wordpress, mcp, novamira, fluent-crm, automation]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [hermes-agent]
---

# WordPress MCP Integration with Novamira

This skill covers connecting a WordPress site running the **Novamira plugin** as an MCP server to Hermes, enabling programmatic access to Fluent CRM, Gutenberg content, WP-CLI, and other WordPress capabilities.

## When to Use

- You have a WordPress site with Novamira plugin installed
- You want to manage Fluent CRM contacts programmatically from Hermes
- You need to automate content, run WP-CLI commands, or execute PHP on the WordPress site
- You want to bulk clean/analyze contacts, create campaigns, or trigger automations

## Prerequisites

1. **Novamira plugin** installed and activated on WordPress
2. **Application Password** created for the WordPress user (Users → Profile → Application Passwords)
3. **MCP endpoint** exposed: `https://your-site.com/wp-json/mcp/novamira`
4. **Hermes** installed locally with MCP support

## Setup: Add WordPress as MCP Server

### 1. Get Connection Details

| Detail | Example |
|--------|---------|
| Server URL | `https://smartmillionaire.co.id/wp-json/mcp/novamira` |
| Username | `yudira` (WordPress username) |
| App Password | `BtFhYh0Z12xvUsSBvmMEyojG` (from WP profile) |
| Transport | `stdio` via `npx @automattic/mcp-wordpress-remote@latest` |

### 2. Add MCP Server to Hermes

```bash
hermes mcp add novamira-smartmillionaire \
  --command npx \
  --args -y @automattic/mcp-wordpress-remote@latest \
  --env WP_API_URL=https://smartmillionaire.co.id/wp-json/mcp/novamira,WP_API_USERNAME=yudira,WP_API_PASSWORD=BtFhYh0Z12xvUsSBvmMEyojG
```

> **Important**: Credentials MUST be passed as env vars (`WP_API_URL`, `WP_API_USERNAME`, `WP_API_PASSWORD`). The package ignores CLI flags like `--url` or `--password`.

### 3. Verify Connection

```bash
hermes mcp test novamira-smartmillionaire
# Should show: ✓ Connected, 3 tools discovered
hermes mcp list
# Should show: novamira-smartmillionaire — enabled
```

> **Note**: If the initial connection test fails and you choose to save the configuration anyway (saved as disabled), you'll need to enable it manually:
> ```bash
> hermes mcp set <server-name> enabled true
> ```
> or via config: `hermes config set mcp_servers.<server-name>.enabled true`

### 4. Config File Format (if editing manually)

In `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  novamira-smartmillionaire:
    command: npx
    args: ["-y", "@automattic/mcp-wordpress-remote@latest"]
    env:
      WP_API_URL: "https://smartmillionaire.co.id/wp-json/mcp/novamira"
      WP_API_USERNAME: "yudira"
      WP_API_PASSWORD: "BtFhYh0Z12xvUsSBvmMEyojG"
    enabled: true
  novamira-leejuan-com:
    command: npx
    args: ["-y", "@automattic/mcp-wordpress-remote@latest"]
    env:
      WP_API_URL: "https://leejuan.com/wp-json/mcp/novamira"
      WP_API_USERNAME: "leejuan"
      WP_API_PASSWORD: "8R8LfKTrlLTIpnka0AiWoUSD"
    enabled: true
```

> **Note**: Args must be a YAML array `["-y", "@automattic/mcp-wordpress-remote@latest"]`, not a string.

### 5. Troubleshooting

- **MCP SDK not installed**: If you see `MCP server '...' requires the 'mcp' Python SDK, but it is not installed`, run:
  ```bash
  /c/Users/pc/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -m pip install mcp
  ```
  (Adjust path to your Hermes venv Python if needed.)

- **Connection saved as disabled**: If the initial test fails and you chose to save the config anyway (disabled), enable it with:
  ```bash
  hermes mcp set <server-name> enabled true
  ```
  or via config: `hermes config set mcp_servers.<server-name>.enabled true`

- **No tools discovered**: The Novamira sandbox directory (`wp-content/novamira-sandbox/`) must not contain any PHP files that output whitespace or echo statements, as they corrupt the JSON-RPC stream. Ensure the sandbox is clean or use `00_bootstrap_cleanup.php` to purge problematic files.

- **Credential format**: Always pass credentials via environment variables (`WP_API_URL`, `WP_API_USERNAME`, `WP_API_PASSWORD`). The `@automattic/mcp-wordpress-remote` package ignores CLI flags like `--url` or `--password`.

## Connecting a NEW Site (no app password on hand)

For a site you've never connected before (e.g. a subdomain like member.smartmillionaire.co.id — a SEPARATE WordPress install from the main domain, with its own DB prefix and credentials):

1. **Find the admin username without auth**: `curl -sL -o /dev/null -w '%{redirect_url}' 'https://site/?author=1'` → redirects to `/author/<username>/`.
2. **Generate an app password over SSH** (faster than walking the user through wp-admin):
   ```bash
   ssh -i ~/.ssh/vps_key -p 2222 root@VPS_IP \
     "cd /www/wwwroot/site && wp user application-password create <user> 'Hermes MCP' --porcelain --allow-root 2>/dev/null"
   ```
   `--porcelain` prints ONLY the password. App passwords are per-install: the same username on two installs has DIFFERENT app passwords — test before assuming.
3. **Verify credentials against the endpoint**: `curl -u 'user:pass' -o /dev/null -w '%{http_code}' https://site/wp-json/mcp/novamira` — valid Basic auth on the route listing returns 200; bare 401 = wrong creds. The MCP route itself is a streamable POST/GET/DELETE endpoint and 401s unauthenticated — that's normal, not a misconfiguration.
4. **`hermes mcp add` prompts interactively** ("Enable all N tools? [Y/n/select]") — in a non-interactive shell this CANCELS and saves nothing. Pipe the answer: `printf 'y\n' | hermes mcp add <name> --command npx --env ... --args -y @automattic/mcp-wordpress-remote@latest`.
5. New MCP tools load only in a new session or via `/reload-mcp`.

## Available Fluent CRM Abilities

After connecting, these abilities are available via `mcp-adapter-execute-ability`:

| Ability | Description |
|---------|-------------|
| `fluent-crm/get-crm-context` | Discovery — returns identity, permissions, stats, tags, lists, triggers, custom fields |
| `fluent-crm/list-contacts` | List/filter contacts with tags + lists inline. Search matches name/email/custom fields |
| `fluent-crm/get-contact` | Full contact profile by ID or email |
| `fluent-crm/upsert-contact` | Create/update contact by ID or email |
| `fluent-crm/bulk-upsert-contacts` | Batch create/update up to 500 contacts |
| `fluent-crm/delete-contact` | Hard-delete contact. Optional `delete_emails` wipes email log |
| `fluent-crm/apply-segments-to-contacts` | Add/remove tags & lists across many contacts. Dry-run first! Cap 5000 |
| `fluent-crm/manage-tag` | Create, update, delete, or merge tags |
| `fluent-crm/manage-list` | Create, update, delete, or merge lists |
| `fluent-crm/list-campaigns` | List campaigns with stats |
| `fluent-crm/upsert-campaign` | Create/update draft campaign |
| `fluent-crm/send-email-to-contact` | Send one-off email to subscribed/transactional contact |

## Common Workflows

### List All Contacts (with pagination)

```bash
# Get first 100 contacts
hermes chat -q "Use Novamira MCP to list first 100 Fluent CRM contacts"
```

Or call MCP directly for debugging:

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-execute-ability","arguments":{"ability_name":"fluent-crm/list-contacts","parameters":{"per_page":100,"page":1}}}}}\n' | WP_API_URL=... WP_API_USERNAME=... WP_API_PASSWORD=... npx -y @automattic/mcp-wordpress-remote@latest
```

### Detect Fake/Suspicious Contacts

Key detection patterns (implemented in session):

```python
# Typo domains
- @gmal.com, @gamil.com, @gmial.com → should be @gmail.com
- @yahooo.com → @yahoo.com
- @dmain.com → @domain.com

# Gibberish/random patterns
- Random consonant strings: tyyurvvbggf, iciciffiff
- Long number sequences: 8020604, 2811, 2361
- Keyboard patterns: qwerty, asdfgh
- Repeated chars: aaaaa, bbbbb

# Name/email mismatch
- Email: spydey2008@gmail.com → Name: "Erwin" (no overlap)
- Email: donywahyudi84@gmail.com → Name: "donywahyudi84@gmail.com" (email as name)

# Disposable domains
- 10minutemail, guerrillamail, mailinator, tempmail, yopmail, etc.
```

### Bulk Delete Suspicious Contacts

```bash
# Delete single contact (with email history)
hermes chat -q "Use Novamira MCP to delete Fluent CRM contact ID 2235 with delete_emails=true"

# Or direct MCP call:
printf '{"jsonrpc":"2.0","id":1,"method":"initialize",...}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-execute-ability","arguments":{"ability_name":"fluent-crm/delete-contact","parameters":{"contact_id":2235,"delete_emails":true}}}}\n' | WP_API_URL=... npx -y @automattic/mcp-wordpress-remote@latest
```

### Create Review List for Manual Inspection

```bash
# 1. Create list
hermes chat -q "Use Novamira MCP to create Fluent CRM list named 'Review'"

# 2. Add suspicious contacts to list
hermes chat -q "Use Novamira MCP to add contacts [2238, 2257, 2261, ...] to list 'Review' (list_id=13)"
```

Or direct:

```bash
# Create list
printf '...{"ability_name":"fluent-crm/manage-list","parameters":{"action":"create","title":"Review","slug":"review-suspicious-contacts"}}...' | npx ...

# Add contacts to list
printf '...{"ability_name":"fluent-crm/apply-segments-to-contacts","parameters":{"add_lists":[13],"contact_ids":[2238,2257,2261,...]}}...' | npx ...
```

## Troubleshooting

### Connection Fails: "Connection closed"

1. **Check endpoint accessibility**:
   ```bash
   curl https://your-site.com/wp-json/mcp/novamira
   # Should return JSON with namespace "mcp" and routes
   ```

2. **Verify credentials**: Test with direct npx call (see above)

3. **Check Novamira settings**: Ensure MCP is enabled in Novamira settings

4. **Firewall/VPN**: If WordPress is on VPS, ensure Hermes can reach it

### Config Not Saved / Wrong Format

- Use `hermes mcp add` CLI command (handles YAML formatting)
- If manual edit: args must be array, env vars as strings
- After config edit: `hermes mcp test <name>` to verify

### MCP Tools Not Showing in Chat

- Restart Hermes session (`/reset` or new `hermes` invocation)
- MCP toolsets load at session start
- Check `hermes mcp list` shows "enabled"

### MCP SDK not installed

If you see `MCP server '...' requires the 'mcp' Python SDK, but it is not installed`, run:
```bash
/c/Users/pc/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -m pip install mcp
```
(Adjust path to your Hermes venv Python if needed.)

### Connection saved as disabled

If the initial test fails and you chose to save the config anyway (disabled), enable it with:
```bash
hermes mcp set <server-name> enabled true
```
or via config: `hermes config set mcp_servers.<server-name>.enabled true`

### No tools discovered

The Novamira sandbox directory (`wp-content/novamira-sandbox/`) must not contain any PHP files that output whitespace or echo statements, as they corrupt the JSON-RPC stream. Ensure the sandbox is clean or use `00_bootstrap_cleanup.php` to purge problematic files.

### Credential format

Always pass credentials via environment variables (`WP_API_URL`, `WP_API_USERNAME`, `WP_API_PASSWORD`). The `@automattic/mcp-wordpress-remote` package ignores CLI flags like `--url` or `--password`.

### MCP Connection Timeouts

If you see `MCP call failed: TimeoutError: MCP stdio subprocess for 'novamira-smartmillionaire' has exited`, this indicates the MCP connection is timing out or the subprocess is crashing. This can happen due to:

1. **Server overload**: The WordPress site may be under heavy load or experiencing PHP execution delays
2. **Sandbox pollution**: As noted in the Novamira instructions, any PHP file in `wp-content/novamira-sandbox/` that outputs whitespace or echo statements will corrupt the JSON-RPC stream and cause MCP failures
3. **Resource limits**: PHP memory limits or execution time limits on the server

**Solutions**:
- Wait a moment and retry - temporary server load may pass
- Check and clean the Novamira sandbox: Ensure `wp-content/novamira-sandbox/` contains only necessary PHP files with no output outside of PHP tags
- Use the `00_bootstrap_cleanup.php` file mentioned in Novamira documentation to purge problematic files
- Consider using Hermes' built-in `novamira/execute-php` ability directly for simple PHP checks when MCP is unstable
- Check server error logs for PHP fatal errors that might be causing the subprocess to exit

### Checking Orders and Commissions

When standard WooCommerce order checks fail (order not found as post ID or WooCommerce order):

1. **Order might be in a custom system**: Check for order-like data in:
   - Bit Flows: `wpz6_bit_pi_flows` and `wpz6_bit_pi_flow_logs` tables
   - FluentCRM/Fluent Cart: `wpz6_fc_orders` table
   - Custom MLM tables: `wpz6_mlm_*` tables

2. **Commission tracking in MLM Binary Pro**:
   - Check `wpz6_mlm_bonuses` table for bonus records
   - Look for `reference_id` containing order numbers or patterns
   - Check `wpz6_mlm_members` for member records
   - Commissions may be stored with status 'pending', 'approved', or 'paid'

3. **Direct SQL checks via MCP**:
   When MCP is unstable, you can still use `novamira/execute-php` to run read-only SQL queries:
   ```php
   // For queries without user-provided values:
   global $wpdb;
   $results = $wpdb->get_results("SELECT * FROM {$wpdb->prefix}mlm_bonuses WHERE status = 'pending'");
   return $results;
   ```
   
   ```php
   // For queries with user-provided values (to prevent SQL injection and syntax errors):
   global $wpdb;
   $order_id = 2900; // Example: checking for a specific order ID
   $sql = $wpdb->prepare("SELECT * FROM {$wpdb->prefix}mlm_bonuses WHERE reference_id = %s", $order_id);
   $results = $wpdb->get_results($sql);
   return $results;
   ```
   
   **Important syntax notes for novamira/execute-php**:
   - Always use double quotes for the PHP string so that `{$wpdb->prefix}` gets properly interpolated
   - When using `$wpdb->prepare()`, match the placeholders (%s for strings, %d for integers) to your variable types
   - Ensure all braces, quotes, and parentheses are properly matched to avoid "Unmatched '}'" errors
   - The `novamira/execute-php` ability expects the entire PHP code as a string, so be careful with nested quotes
   - Test your PHP code locally first if possible to catch syntax errors before sending via MCP
   
   Always use `$wpdb->prepare()` for user-provided values to prevent SQL injection.

4. **Alternative access methods**:
   - If MCP persistently fails, use WordPress REST API directly with application passwords
   - Check WooCommerce orders page in WP-admin for visual confirmation
   - Use Fluent CRM contact list to see if purchase activity is recorded there
## Using Novamira CLI (Alternative)

You can also use the Novamira CLI tool directly to interact with the WordPress site without configuring an MCP server. See the `hermes-agent` skill for installation and usage details.


## References

- [Novamira Plugin](https://novamira.com/) — WordPress AI automation plugin
- [Fluent CRM](https://fluentcrm.com/) — Self-hosted email marketing automation
- [MCP Spec](https://modelcontextprotocol.io/) — Model Context Protocol
- [Hermes MCP Docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)

## Pitfalls & Gotchas

| Issue | Solution |
|-------|----------|
| Args as string not array | Use `["-y", "pkg"]` not `"[\"-y\", \"pkg\"]"` |
| Credentials in CLI flags | Use env vars only: `WP_API_URL`, `WP_API_USERNAME`, `WP_API_PASSWORD` |
| Config not reloading | Restart Hermes session (`/reset`) |
| Large contact lists timeout | Use pagination (per_page=100), fetch in batches |
| Deleted contacts still in list | Lists auto-clean on contact delete, but verify |
| VPS WordPress not reachable | Use ngrok/cloudflare tunnel for local Hermes → VPS WordPress |
| `hermes mcp add` silently cancels | The tool-selection prompt cancels when non-interactive — pipe `printf 'y\n' |` into it |
| App password for one site fails on its subdomain | Each WP install has its own app passwords; generate one per install via WP-CLI |
| `wp eval`/`eval-file` can't inspect the admin menu | `admin_menu` never fires in CLI, so `$menu`/`$submenu` are empty — verify menu registration by reading the plugin's menu-registration code or loading wp-admin in a browser, not via wp eval |

## Session Artifacts

See `references/` directory for:
- `fake-detection-patterns.md` — Complete detection rules used
- `contact-analysis-session.md` — Full transcript of 2287 contact analysis
- `mcp-direct-calls.md` — Raw npx command examples for debugging