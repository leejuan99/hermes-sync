# MCP Direct Calls — Raw npx Command Examples

Raw JSON-RPC commands for calling the Novamira MCP server directly via `npx @automattic/mcp-wordpress-remote@latest`.

Use these for debugging, testing, or when Hermes chat is unavailable.

## Environment Setup

```bash
export WP_API_URL="https://smartmillionaire.co.id/wp-json/mcp/novamira"
export WP_API_USERNAME="yudira"
export WP_API_PASSWORD="BtFhYh0Z12xvUsSBvmMEyojG"
export PATH="/c/Program Files/nodejs:$PATH"
```

Or inline:
```bash
WP_API_URL=... WP_API_USERNAME=... WP_API_PASSWORD=... /c/Program\ Files/nodejs/npx.cmd -y @automattic/mcp-wordpress-remote@latest
```

## Initialize Connection

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}\n' | WP_API_URL=... WP_API_USERNAME=... WP_API_PASSWORD=... npx -y @automattic/mcp-wordpress-remote@latest
```

**Expected response**:
```json
{"result":{"protocolVersion":"2024-11-05","serverInfo":{"name":"Novamira","version":"v1.0.0"},"capabilities":{"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":false}},"instructions":"Default MCP server for WordPress abilities discovery and execution"},"jsonrpc":"2.0","id":1}
```

## List Abilities (Discover)

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize",...}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-discover-abilities","arguments":{}}}\n' | npx ...
```

## Execute Any Ability

**Template**:
```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize",...}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-execute-ability","arguments":{"ability_name":"ABILITY_NAME","parameters":{}}}}\n' | npx ...
```

### Fluent CRM Examples

#### Get CRM Context (run once per session)
```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-execute-ability","arguments":{"ability_name":"fluent-crm/get-crm-context","parameters":{}}}}\n' | npx ...
```

#### List Contacts (paginated)
```bash
# Page 1, 100 per page
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-execute-ability","arguments":{"ability_name":"fluent-crm/list-contacts","parameters":{"per_page":100,"page":1}}}}\n' | npx ...

# Page N
... "parameters":{"per_page":100,"page":N} ...
```

#### Get Single Contact
```bash
printf '...{"ability_name":"fluent-crm/get-contact","parameters":{"contact_id":2235}}...' | npx ...
# Or by email:
printf '...{"ability_name":"fluent-crm/get-contact","parameters":{"email":"user@example.com"}}...' | npx ...
```

#### Delete Contact
```bash
printf '...{"ability_name":"fluent-crm/delete-contact","parameters":{"contact_id":2235,"delete_emails":true}}...' | npx ...
```

#### Create List
```bash
printf '...{"ability_name":"fluent-crm/manage-list","parameters":{"action":"create","title":"Review","slug":"review-suspicious-contacts"}}...' | npx ...
```

#### Add Contacts to List
```bash
printf '...{"ability_name":"fluent-crm/apply-segments-to-contacts","parameters":{"add_lists":[13],"contact_ids":[2238,2257,2261,...]}}...' | npx ...
```

#### Bulk Upsert Contacts
```bash
printf '...{"ability_name":"fluent-crm/bulk-upsert-contacts","parameters":{"contacts":[{"email":"new@example.com","first_name":"Test","tags":["lead"],"lists":[12]},...]}}...' | npx ...
```

#### List Campaigns
```bash
printf '...{"ability_name":"fluent-crm/list-campaigns","parameters":{}}...' | npx ...
```

#### Send Test Email
```bash
printf '...{"ability_name":"fluent-crm/send-test-email","parameters":{"campaign_id":123,"to_email":"test@example.com"}}...' | npx ...
```

## Full Pipeline: Fetch All Contacts (23 pages)

```bash
#!/bin/bash
WP_API_URL="https://smartmillionaire.co.id/wp-json/mcp/novamira"
WP_API_USERNAME="yudira"
WP_API_PASSWORD="BtFhYh0Z12xvUsSBvmMEyojG"

for page in {1..23}; do
  printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"mcp-adapter-execute-ability","arguments":{"ability_name":"fluent-crm/list-contacts","parameters":{"per_page":100,"page":%d}}}}\n' $page | \
  WP_API_URL=$WP_API_URL WP_API_USERNAME=$WP_API_USERNAME WP_API_PASSWORD=$WP_API_PASSWORD \
  /c/Program\ Files/nodejs/npx.cmd -y @automattic/mcp-wordpress-remote@latest 2>&1 | tail -1 > page_$page.json
  echo "Page $page done"
done
```

## Parse Response

The response has two JSON-RPC objects (initialize + tool result). Extract the second:

```python
import json

with open('page_1.json') as f:
    content = f.read().strip()

# Split by newline, second line is the tool result
lines = content.strip().split('\n')
tool_result = json.loads(lines[1])

# The actual data is double-encoded in content[0].text
text_content = tool_result['result']['content'][0]['text']
data = json.loads(text_content)

items = data['data']['items']  # List of contacts
total = data['data']['total']
page = data['data']['page']
```

## Troubleshooting Commands

### Test Endpoint Directly
```bash
curl https://smartmillionaire.co.id/wp-json/mcp/novamira
# Should return JSON with namespace "mcp" and routes
```

### Check WP REST API
```bash
curl https://smartmillionaire.co.id/wp-json/
# Shows all namespaces including "novamira/v1", "mcp"
```

### Test Credentials
```bash
curl -u "yudira:BtFhYh0Z12xvUsSBvmMEyojG" https://smartmillionaire.co.id/wp-json/wp/v2/users/me
# Should return user info
```

### Debug MCP Connection
```bash
# Run with verbose output
WP_API_URL=... WP_API_USERNAME=... WP_API_PASSWORD=... npx -y @automattic/mcp-wordpress-remote@latest 2>&1
# Type initialize request manually, watch for errors
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Connection closed` | Endpoint unreachable / auth failed | Check URL, credentials, firewall |
| `WordPress connection timed out` | Slow VPS / network | Increase timeout, check VPS load |
| `Ability not found` | Wrong ability name | Use `mcp-adapter-discover-abilities` first |
| `filter is required` | `estimate-dynamic-segment` needs filter | Provide filter parameter |
| `Cannot process tools/call` | Init not completed | Send initialize first, then tools/call in same session |

## Rate Limits

- **Per page**: 100 contacts max
- **Batch operations**: 500 contacts max (bulk upsert)
- **Apply segments**: 5000 contacts max
- **Timeout**: ~30s per call, use batch for large ops

## Notes

- Always send `initialize` first in each npx invocation
- The MCP server is stateless — each npx call is independent
- For bulk operations, prefer `hermes chat` which maintains session
- Direct npx is best for: debugging, CI/CD, one-off scripts