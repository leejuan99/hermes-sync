# Gumroad CLI Cheatsheet

## Installation

```bash
# macOS (Homebrew)
brew install antiwork/cli/gumroad

# Linux/WSL (install script)
curl -fsSL https://gumroad.com/install-cli.sh | bash

# Go
go install github.com/antiwork/gumroad-cli/cmd/gumroad@latest

# Binary download (Linux x64)
wget https://github.com/antiwork/gumroad-cli/releases/latest/download/gumroad_linux_amd64.tar.gz
tar -xzf gumroad_linux_amd64.tar.gz
sudo mv gumroad /usr/local/bin/
```

## Authentication

### Interactive (Device Authorization) - Recommended for VPS
```bash
gumroad auth login --web
# Opens browser to https://app.gumroad.com/oauth/authorize?...
# User approves → token saved to ~/.config/gumroad/seller_token
```

### Non-Interactive (CI / Agents)
```bash
# Option 1: Pipe token
echo "your_seller_token" | gumroad auth login --with-token

# Option 2: Environment variable (takes precedence)
export GUMROAD_ACCESS_TOKEN="your_seller_token"
gumroad user  # works without stored config
```

### Check Status
```bash
gumroad auth status
# Shows: seller authenticated, admin authenticated, token preview
```

### Logout
```bash
gumroad auth logout  # Revokes and deletes stored tokens
```

## Product Commands

```bash
# List products (paginated, use --all for all)
gumroad products list --all --json

# View single product
gumroad products view <product_id> --json

# Create product (minimum required: name, url)
gumroad products create \
  --name "Product Name" \
  --url "https://example.com/download" \
  --description "Product description" \
  --price 0 \
  --json

# Create with all options
gumroad products create \
  --name "Course Title" \
  --url "https://download.link" \
  --description "Full description here" \
  --price 29.99 \
  --currency USD \
  --custom-permalink "my-course" \
  --tags "tag1,tag2" \
  --published true \
  --json

# Update product
gumroad products update <product_id> \
  --name "New Name" \
  --price 39.99 \
  --json

# Delete product
gumroad products delete <product_id> --confirm
```

## Output Formats

| Flag | Output | Use Case |
|------|--------|----------|
| (default) | Colored table | Human reading |
| `--json` | Full JSON | Programmatic parsing |
| `--jq <expr>` | Filtered JSON | Extract specific fields |
| `--plain` | Tab-separated | Piping to grep/awk |
| `--quiet` | Minimal | Scripts |

## Common Patterns for Automation

### Create product from variables (n8n Execute Command)
```bash
gumroad products create \
  --name "{{$json.title}}" \
  --description "{{$json.description || $json['content:encoded'] || 'Auto-imported'}}" \
  --url "{{$json.link}}" \
  --json
```

### Parse JSON output in n8n Function node
```javascript
// stdout from Execute Command contains JSON
const result = JSON.parse($json.stdout);
return [{
  json: {
    productId: result.product.id,
    productUrl: result.product.permalink_url,
    price: result.product.price
  }
}];
```

### Filter products with jq
```bash
# Get only published product IDs and names
gumroad products list --all --json --jq '.products[] | select(.published == true) | {id, name}'

# Get sales summary by month
gumroad sales summary --group-by month --from 2026-01-01 --json
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GUMROAD_ACCESS_TOKEN` | Seller access token (overrides stored config) |
| `GUMROAD_ADMIN_TOKEN` | Admin token (for admin commands) |
| `GUMROAD_ADMIN_API_BASE_URL` | Custom API base (local testing) |

## Token Storage Locations

| OS | Path |
|----|------|
| Linux/macOS | `~/.config/gumroad/seller_token` |
| Windows | `%APPDATA%\gumroad\seller_token` |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `not_authenticated` with admin token | Use `GUMROAD_ACCESS_TOKEN` (seller token), not admin token |
| `command not found` | Add binary to PATH or use absolute path `/usr/local/bin/gumroad` |
| Permission denied | `chmod +x /usr/local/bin/gumroad` |
| Rate limited | Add `--page-delay 500ms` to paginated commands |