# GreenCloud + aaPanel SSH Setup Guide

## Complete Step-by-Step for Users Who Struggle with CLI

### Phase 1: Generate SSH Keys (Local Machine)

```bash
# Windows PowerShell or Command Prompt
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vps_key -C "vps-connection"
# Press Enter for no passphrase (or add one for extra security)
```

**Output expected:**
```
Your identification has been saved in C:\Users\pc\.ssh\vps_key
Your public key has been saved in C:\Users\pc\.ssh\vps_key.pub
```

**Copy the PUBLIC key (not private!):**
```bash
type ~/.ssh\vps_key.pub
```

### Phase 2: Add Key in GreenCloud Panel

1. Login to GreenCloud control panel
2. Navigate to **SSH Keys** → **Add SSH Key**
3. **Name:** `vps-key-hermes` (or any name)
4. **Paste public key** (entire output from step 1, starts with `ssh-rsa AAAA...`)
5. **Save**

### Phase 3: CRITICAL - Full VPS Restart

**GreenCloud requires full restart for SSH key propagation.**

In GreenCloud panel:
1. Go to **VPS Details** → **Control** tab
2. Click **Restart** (not just reboot from inside)
3. **Wait 90-120 seconds** - GreenCloud takes longer than DigitalOcean
4. Verify status shows **Running** with green indicator

### Phase 4: Open Port 22 in ALL THREE Firewalls

#### A. Internal UFW (via aaPanel Terminal - EASIEST)
1. Login to aaPanel: `http://194.127.192.52:8888` (or port 26676 with token)
2. Go to **Terminal** → **Local Server**
3. Run:
```bash
ufw allow 22/tcp
ufw reload
ufw status
```
Expected: `22/tcp  ALLOW  Anywhere`

#### B. aaPanel Built-in Firewall (REQUIRED!)
**Even if UFW allows port 22, aaPanel's firewall blocks by default.**

1. In aaPanel → **Security** → **Firewall**
2. Click **Add Port Rule**:
```
Protocol: TCP
Port: 22
Direction: All
Action: Allow
Remarks: SSH Access
```
3. Click **Confirm**

#### C. External GreenCloud Panel Firewall (REQUIRED!)
**Even if both UFW and aaPanel allow port 22, GreenCloud's external firewall blocks by default.**

1. In GreenCloud panel → VPS → **Options** tab
2. Look for **Firewall** / **Security Rules** / **Port Rules**
3. Click **Add Rule**:
```
Protocol: TCP
Port: 22
Source: 0.0.0.0/0 (or your IP for security)
Action: Allow
Description: SSH Access
```
4. **Save/Apply**

### Phase 5: Test SSH Connection

```bash
# From local terminal
ssh -i ~/.ssh/vps_key root@194.127.192.52 "uptime"
```

**Expected output:**
```
 12:34:56 up 5 days,  2 users,  load average: 0.15, 0.10, 0.05
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` | VPS still booting | Wait 60s, retry |
| `Connection timed out` | Firewall blocking | Check ALL THREE firewalls: UFW, aaPanel, GreenCloud |
| `Permission denied` | Wrong key / key not propagated | Verify key in aaPanel terminal: `cat ~/.ssh/authorized_keys` |
| `ssh: connect to host... port 22: Connection refused` | SSH service not running | In aaPanel terminal: `systemctl restart ssh` |

### Quick Reference: GreenCloud Panel Navigation

| Task | Menu Path |
|------|-----------|
| Add SSH Key | Dashboard → SSH Keys → Add |
| VPS Restart | VPS List → Click VPS → Control → Restart |
| External Firewall | VPS → Options → Firewall / Security Rules |
| VNC Console | VPS → VNC / Console button |
| VPS Details | VPS List → Click VPS name |

### Quick Reference: aaPanel Firewall Navigation

| Task | aaPanel Menu Path |
|------|-------------------|
| Add Port Rule | **Security** → **Firewall** → **Add Port Rule** → Protocol: TCP, Port: 22, Direction: All directions: All, Action: Allow → **Confirm** |
| Check UFW Status | **Terminal** → Local Server → `ufw status` |
| Open UFW Port | **Terminal** → Local Server → `ufw allow 22/tcp && ufw reload` |

---

## For GUI-Preferred Users (No SSH Required)

**Use aaPanel for everything:**

| Task | aaPanel Menu |
|------|--------------|
| File Management | **Files** → Browse `/www/wwwroot/` |
| Terminal/Commands | **Terminal** → Local Server |
| Database | **Databases** → phpMyAdmin |
| Websites/SSL | **Website** → Manage |
| Logs/Errors | **Logs** |
| Cron Jobs | **Cron** |
| Services Restart | **Home** → Restart buttons |

**This avoids SSH entirely!** Recommended for users who say "susah njir bray" with CLI.