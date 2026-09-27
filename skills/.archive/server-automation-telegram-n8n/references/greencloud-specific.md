# GreenCloud VPS Provider Specifics

## External Firewall (Critical!)

**GreenCloud has an external firewall at the provider level** that blocks ports BEFORE they reach your VPS's UFW.

### What This Means:
- You can open port 22 in UFW all day, but GreenCloud's external firewall will still block it
- You MUST configure firewall rules in **GreenCloud Control Panel** → Your VPS → Network/Firewall/Security Group
- This is separate from UFW (which is host-level)

### How to Configure:
1. Login to GreenCloud billing panel: `https://greencloudvps.com/billing/login`
2. Go to **Services** → **My Services** → Click your VPS
3. Look for **Network**, **Firewall**, **Security Group**, or **Port Rules** tab
4. Add rules:
   ```
   Protocol: TCP
   Port: 22 (or 2222 for SSH)
   Source: 0.0.0.0/0 (or your IP only)
   Action: Allow
   ```

### Verification:
```bash
# From LOCAL machine (not VPS):
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 uptime
# If timeout → external firewall blocking
# If "Permission denied" → SSH config/key issue
```

## GreenCloud Control Panel Layout

Based on session screenshots, the panel has these tabs:
- **Overview** - Server status, CPU/RAM/Network graphs
- **Media** - ISO mounting, etc.
- **Options** - VNC, Rescue, Password, Settings, Boot Type, Auto Config
- **Network** - IP addresses (IPv4/IPv6), DNS resolvers
- **Storage** - Disk management
- **Backups** - Snapshot/backup management
- **Sharing** - Access tokens, SSH keys

### Key Buttons:
- **Boot/Shutdown/Restart/Power Off/Rebuild** - Power controls
- **VNC Console** - Access via browser (port 6002, password visible in UI)
- **SSH Keys** - Add/remove authorized keys

## SSH Key Management

GreenCloud has an **SSH Keys panel** (separate from VPS panel):
- Access via main navigation: **SSH Keys**
- **Add SSH Key** dialog: Name + Public Key (RSA 2048-bit shown)
- Keys added here get injected into VPS on next boot/rebuild
- Can add multiple keys

## VNC Console Notes

- URL format: `http://96.9.210.14:6002` (varies per VPS)
- Password shown in UI (click eye icon to reveal)
- **Password input in VNC terminal shows NO characters** - this is normal Linux behavior
- Type blindly, press Enter

## aaPanel Integration

GreenCloud VPS comes with aaPanel pre-installed on port 26676:
- URL: `https://your-domain:26676/random-token`
- Default user/pass: Need to check aaPanel install logs or reset
- Manages: Websites, Databases, Files, Terminal, Cron, Security (UFW wrapper)

## Network Details (from session)

```
IPv4: 194.127.192.52
IPv6: 2402:a7c0:8100:a017::2b6:0/112
Gateway: 194.127.192.1
Netmask: 255.255.254.0
DNS: 8.8.8.8, 8.8.4.4
Location: Singapore DC2 (SG2-ROME3)
```

## Provider-Level Port Blocks Confirmed

| Port | External Firewall | UFW | Result |
|------|-------------------|-----|--------|
| 22   | BLOCKED           | ALLOW | ❌ Timeout |
| 2222 | Must allow        | ALLOW | ✅ Works |
| 26676 | Must allow       | ALLOW | ✅ Works (aaPanel) |
| 5678 | Must allow        | ALLOW | ✅ Works (n8n) |
| 3306 | Must allow        | DENY  | ✅ Blocked correctly |

## Key Takeaways for Future Sessions

1. **Always check provider firewall first** - UFW changes won't help if provider blocks
2. **GreenCloud = external firewall** - must configure in billing panel
3. **VNC is your escape hatch** - when SSH completely blocked
4. **aaPanel UFW wrapper** - sync with manual UFW rules
5. **SSH key injection** - via GreenCloud SSH Keys panel, not just `authorized_keys`