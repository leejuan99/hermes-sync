# GreenCloud Firewall Navigation

## Access
1. Login: `https://greencloudvps.com/billing/login`
2. Click VPS → Network / Security / Firewall

## Common Tab Names
- **Network** → Port Forwarding / Security Rules
- **Security** → Firewall Rules / Security Groups
- **Firewall** (may be standalone tab)

## Adding Rules
```
Protocol: TCP
Port: 22 (SSH), 80 (HTTP), 443 (HTTPS), 5678 (n8n), etc.
Source: 0.0.0.0/0 (or specific IP)
Action: Allow / Accept
Description: SSH Access / n8n / etc.
```

## Verification
After adding rule, test from local:
```bash
ssh -i ~/.ssh/vps_key root@<VPS_IP> uptime
```

## Notes
- Rules take effect immediately (no restart needed)
- If "No firewall rules found" → check Security Groups or Network Security
- Some VPS have "Security Group" that must be attached to instance