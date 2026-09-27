# aaPanel Firewall Configuration

## Access
aaPanel → Security → Firewall

## Interface Overview
- **Firewall** toggle: ON/OFF (must be ON)
- **Block ICMP** toggle: ON/OFF
- **Port Rules** table: Shows existing rules
- **Add Port Rule** button: Create new rule
- **Direction**: All directions / Inbound / Outbound

## Adding Port Rule
1. Click **Add Port Rule**
2. Fill form:
   - **Protocol**: TCP (or UDP if needed)
   - **Port**: 22, 80, 443, 5678, etc.
   - **Source IP**: All (0.0.0.0/0) or specific IP
   - **Strategy**: Allow
   - **Direction**: Inbound (or All directions)
   - **Remarks**: Description (e.g., "SSH", "n8n", "HTTP")
3. Click **Confirm**

## Common Rules for n8n VPS
| Port | Protocol | Direction | Remarks |
|------|----------|-----------|---------|
| 22 | TCP | Inbound | SSH |
| 80 | TCP | Inbound | HTTP |
| 443 | TCP | Inbound | HTTPS |
| 5678 | TCP | Inbound | n8n |
| 26676 | TCP | Inbound | aaPanel |

## Verification
```bash
# Check UFW (internal firewall)
ufw status

# Check listening ports
netstat -tlnp | grep :22
netstat -tlnp | grep :5678
```

## Notes
- aaPanel firewall rules persist across reboots
- Works alongside GreenCloud external firewall (both must allow)
- Rules take effect immediately
- Can export/import rules via buttons