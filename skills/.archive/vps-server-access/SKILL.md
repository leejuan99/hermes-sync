---
name: vps-server-access
title: VPS Server Access & Remote Management
description: |
  Methods to access and manage a remote VPS — SSH, web control panels (aaPanel/cPanel/Plesk), 
  FTP/SFTP, VNC console. How to choose the right access method based on user preference, 
  available tools, and frustration signals. Covers GreenCloud, DigitalOcean, and similar VPS 
  providers with auto-provisioned panels.
triggers:
  - User needs SSH access to a VPS
  - User is setting up remote server access
  - SSH connection fails or is blocked
  - User expresses frustration with CLI-based access methods
  - VPS provider offers multiple access options
keywords:
  - VPS access
  - SSH key setup
  - remote server management
  - aaPanel, cPanel, Plesk
  - FTP/SFTP
  - web terminal
---

# VPS Server Access & Remote Management

## Quick Reference: Access Methods by Preference

| Method | Use When | Preference |
|--------|----------|-----------|
| **Web Panel Terminal** | Panel already provisioned (aaPanel/cPanel/Plesk) — **PREFERRED for most users** | GUI-preferring users, less frustration, zero setup |
| **SSH via CLI** | Power user, scripting, no GUI available | CLI-savvy users |
| **FTP/SFTP** | File upload/management, simplest setup | Visual file transfer |
| **VNC Console** | Emergency access, reinstall, troubleshooting | Last resort, unencrypted |

**⚡ Priority order when panel exists:** Web Panel Terminal → SSH → VNC Console → FTP

---

## Workflow: Choosing the Right Access Method

### Step 1: Identify Available Access Methods
For each VPS provider (GreenCloud, DigitalOcean, AWS, etc.):
- **Check for web control panel** first — aaPanel, cPanel, Plesk are common
- **Verify SSH is available** — check firewall/security groups for port 22
- **Check for VNC/console** — for emergency access
- **Ask provider** if unclear — their support can clarify

### Step 2: Match Method to User Type

**GUI-preferring users (especially when frustrated with CLI):**
- ✅ Redirect to web panel terminal/file manager immediately
- ✅ Offer FTP for file transfer
- ✅ Use panel for WordPress/PHP debugging, config edits, database access
- ❌ Avoid prolonged SSH debugging; pivot to GUI tool

**CLI-savvy users:**
- ✅ SSH is fine
- ✅ Proceed with key-based auth setup

**When user shows frustration signals:**
- "This is complicated", "too hard", "just make it work" → **Pivot to GUI tool**
- Don't persist with CLI troubleshooting if a panel exists
- **User speaks casual Indonesian** - respond in same register (bahasa informal, 'bray', 'lo/gua')
- **Prefers desktop GUI apps over CLI scripts** - default to web panel when available
- **Gets frustrated with technical complexity** - prefers quick, direct action over lengthy explanation


### Step 3: SSH Key Setup (if SSH chosen)

#### Generate new key pair (never reuse shared keys):
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vps_key -C "vps-connection"
cat ~/.ssh/vps_key.pub  # Public key only — share this
```

#### Add public key to VPS:
1. **Via panel:** SSH Keys section → paste `.pub` content → Save/Apply
2. **Via CLI:** SSH with password → edit `~/.ssh/authorized_keys` → paste `.pub`
3. **Restart VPS** after adding key (required for some providers)

#### Test connection:
```bash
ssh -i ~/.ssh/vps_key user@VPS_IP
ssh -v -i ~/.ssh/vps_key user@VPS_IP  # Verbose for debugging
```

---

## Common Issues & Solutions

### SSH Connection Timeout
**Cause:** Port 22 blocked, SSH not running, firewall rule missing  
**Fix:**
1. Check firewall/security group allows port 22
2. Verify VPS is running (restart if needed)
3. Try VNC console or web panel terminal as fallback

### Permission Denied (Publickey)
**Cause:** Public key not in `authorized_keys` or format mismatch  
**Fix:**
1. Check key exists: `cat ~/.ssh/authorized_keys` on server
2. Verify it matches your `.pub` file exactly
3. Restart SSH service: `systemctl restart ssh`
4. If using panel: Re-apply SSH key, then restart VPS

### SSH Key Won't Load
**Cause:** Key path wrong, permissions incorrect, key format incompatible  
**Fix:**
```bash
ssh-keygen -l -f ~/.ssh/vps_key        # Check key exists
ls -la ~/.ssh/vps_key                  # Should be readable
ssh-key-convert (if needed)            # Convert PuTTY to OpenSSH if applicable
```

---

### GreenCloud + aaPanel Specifics

**Full troubleshooting guide:** See `references/greencloud-aapanel-ssh-setup.md`
**WordPress performance debugging:** See `references/wordpress-performance-debug-aapanel.md`

### aaPanel Auto-Provisioning
- aaPanel is often pre-installed and running on port 8888
- Web panel URL: `http://VPS_IP:8888`
- aaPanel has built-in SSH key management and terminal
- **Preferred workflow for GUI users:** Use aaPanel terminal instead of SSH

### GreenCloud SSH Key Propagation
- **Critical:** SSH keys require **full VPS restart** after adding (DigitalOcean is 30s, GreenCloud is 1-2 min)
- Add key in panel → Save → **Restart VPS** → Wait 90–120 seconds → Test SSH
- If immediate SSH test fails with "Connection refused", server is still booting — wait and retry
- Port 22 may be blocked by default — check Firewall/Security rules in panel

### ⚠️ GreenCloud External Firewall (Important!)
**GreenCloud has THREE firewall layers:**
1. **Internal UFW** (on the VPS itself) - managed via aaPanel terminal or CLI
2. **aaPanel Built-in Firewall** (Security → Firewall → Port Rules) - web panel level
3. **External GreenCloud Panel Firewall** (provider-level) - managed in GreenCloud control panel

**All THREE must allow port 22!** Even if UFW shows `22/tcp ALLOW`, external connections will timeout if any layer blocks it.

**Fix Order:**
1. **UFW (Internal):** aaPanel Terminal → `ufw allow 22/tcp && ufw reload`
2. **aaPanel Firewall:** Security → Firewall → **Add Port Rule** → TCP 22 → Allow → All directions → Confirm
3. **GreenCloud External Firewall:** GreenCloud panel → VPS → **Options** tab → **Firewall/Security Rules** → Add rule:
```
Protocol: TCP
Port: 22
Source: 0.0.0.0/0 (or your IP)
Action: Allow
```

**Test flow:**
1. UFW allows port 22 → ✅
2. SSH service running → ✅ 
3. authorized_keys configured → ✅
4. **aaPanel Firewall allows 22** → ✅
5. **GreenCloud firewall allows 22** → ✅ = SSH works

### SSH Key Management in aaPanel
- aaPanel auto-syncs keys to `~/.ssh/authorized_keys`
- Key activation: Add in panel → **must restart VPS** for key to take effect
- Old keys: Remember to **remove compromised keys** from authorized_keys via panel

### Access VPS via aaPanel:
1. Open `http://VPS_IP:8888`
2. Login with aaPanel credentials (sent via email or reset via GreenCloud)
3. Click **"Terminal"** in sidebar
4. Full CLI access without SSH setup

### WordPress Performance Debugging via aaPanel
When user reports slow WordPress loading or FOUC/layout shift:
1. **Files** → Navigate to `/www/wwwroot/DOMAIN/` → Check `wp-content/plugins/` for heavy plugins
2. **Terminal** → Run:
   ```bash
   # Check error logs
   tail -f /www/wwwlogs/DOMAIN.error.log
   
   # Check plugin sizes
   du -sh /www/wwwroot/DOMAIN/wp-content/plugins/*
   
   # PHP-FPM status
   systemctl status php-fpm-83
   
   # Check active theme and plugin enqueue order
   grep -r "wp_enqueue_style\|wp_enqueue_script" /www/wwwroot/DOMAIN/wp-content/themes/ACTIVE_THEME/
   grep -r "wp_enqueue_style\|wp_enqueue_script" /www/wwwroot/DOMAIN/wp-content/plugins/PROBLEM_PLUGIN/
   ```
3. **Databases** → phpMyAdmin/Adminer → Check for bloat, slow queries
4. **PHP version** → Switch or configure OPcache/JIT in Website → PHP version
5. **Website → Conf** → Enable LSCache/OpenLiteSpeed cache rules
6. **Monitor** → Check CPU/RAM/Disk for resource pressure

### Fixing FOUC (Flash of Unstyled Content) / Layout Shift via aaPanel
When WordPress page shows broken layout before CSS loads:

**Root Causes:**
- Plugin CSS loads AFTER page content (WP Webinar System, page builders, etc.)
- No critical CSS inlined
- OpenLiteSpeed not serving cache properly
- Theme loads CSS via `wp_head()` without proper dependencies

**Debug Steps via aaPanel Terminal:**
```bash
# 1. Identify active theme
ls /www/wwwroot/DOMAIN/wp-content/themes/

# 2. Check theme's functions.php for enqueue order
grep -A 30 "wp_enqueue_scripts" /www/wwwroot/DOMAIN/wp-content/themes/THEME/functions.php

# 3. Check problematic plugin's enqueue
grep -r "wp_enqueue_style\|wp_enqueue_script" /www/wwwroot/DOMAIN/wp-content/plugins/PLUGIN_NAME/

# 4. Check if LSCache is enabled for site
cat /www/server/panel/vhost/openlitespeed/DOMAIN.conf | grep -i cache
```

**Fix Options (apply via aaPanel Files → Edit):**

**Option A: Inline Critical CSS + Hide Until Ready (in theme's functions.php or mu-plugin):**
```php
add_action('wp_head', 'fix_fouc_for_page', 1);
function fix_fouc_for_page() {
    if (is_page('smart-webinar') || strpos(get_permalink(), 'smart-webinar') !== false) {
        echo '<style id="fouc-fix">body{opacity:0;visibility:hidden}html{visibility:visible}</style>';
        echo '<script>(function(){var s=document.getElementById("fouc-fix");document.addEventListener("DOMContentLoaded",function(){s.remove();document.body.style.opacity="1";document.body.style.visibility="visible"});setTimeout(function(){s.remove();document.body.style.opacity="1";document.body.style.visibility="visible"},3000)})()</script>';
    }
}
```

**Option B: Force plugin CSS to load earlier via dependency:**
```php
add_action('wp_enqueue_scripts', 'fix_plugin_css_order', 1);
function fix_plugin_css_order() {
    if (is_page('smart-webinar')) {
        wp_add_inline_style('theme-main-style', '.wpws-container,.wpws-webinar-header,.wpws-registration-form{visibility:hidden}.wpws-loaded .wpws-container,.wpws-loaded .wpws-webinar-header,.wpws-loaded .wpws-registration-form{visibility:visible}');
    }
}
```

**Option C: Enable OpenLiteSpeed LSCache (Best Long-term):**
1. aaPanel → **Website** → Click site → **Conf** → **LSCache** → Enable
2. Install **LiteSpeed Cache** plugin in WordPress
3. Configure: Preset → "Standard" or "Advanced" → Save → Purge All

**Quick Verification:**
```bash
# After fix, test curl for render-blocking CSS
curl -I https://DOMAIN/page-slug/
# Check for Cache-Control, Content-Encoding: br/gzip
```

### VNC Console for Emergency Access
- GreenCloud panel: VPS Management → Console/VNC
- Browser-based VNC (port 6001+)
- Password shown in panel
- Full root shell without SSH keys

---

## Pitfalls

🔴 **Never share private keys** — if shared (even to chat), treat as compromised  
🔴 **Don't reuse SSH keys** across VPS instances — generate unique key per server  
🔴 **Firewall port 22 blocked** — SSH will timeout silently; check security groups first  
🔴 **Forgot to restart VPS** after adding SSH key — key won't activate  
🔴 **CLI-only when GUI exists** — for frustrated users, offer panel terminal/file manager immediately  
🔴 **SSH key format mismatch** — PuTTY vs OpenSSH; aaPanel/Linux expect OpenSSH format  

---

## Support Files

| Type | File | Purpose |
|------|------|---------|
| **Reference** | `references/greencloud-aapanel-ssh-setup.md` | GreenCloud + aaPanel SSH key propagation specifics |
| **Reference** | `references/wordpress-performance-debug-aapanel.md` | WordPress performance debugging via aaPanel |
| **Reference** | `references/smart-webinar-fouc-fix-session.md` | Session-specific: WP Webinar System FOUC fix on GreenCloud/aaPanel |
| **Template** | `templates/fouc-fix-template.php` | Reusable FOUC fix template - customize for any plugin/page |
| **Script** | `scripts/verify-fouc-fix.sh` | Verification script - run via aaPanel terminal after FOUC fix |

---

## When to Use Web Panel vs SSH

| Scenario | Best Tool |
|----------|-----------|
| First-time access | Web panel (if available) |
| File upload/download | FTP via panel or web file manager |
| User frustrated with CLI | Web panel terminal immediately |
| Scripting/automation | SSH on stable key |
| Emergency/locked out | VNC console |
| Bulk server ops | SSH + scripting |
| WordPress/PHP performance debug | **Web panel terminal + File Manager** — check plugins, cache, logs, config without SSH |
| Database optimization | Web panel → Databases → phpMyAdmin/Adminer |
| Quick config edits | Web panel → Files → Edit |

---

## Quick Checklist

- [ ] Identify all access methods available (SSH, panel, FTP, VNC)
- [ ] Match access method to user preference (GUI vs CLI)
- [ ] If SSH chosen: generate new key, add to authorized_keys, restart VPS
- [ ] Test connection; if timeout, check firewall before SSH
- [ ] If CLI frustrating user: pivot to web panel terminal immediately
- [ ] Remove compromised/old keys from authorized_keys

## Session Learnings (2026-06-28)

### SSH Key Details
- **Key format matters**: aaPanel/Linux expects OpenSSH format (`ssh-rsa AAAA...` or `ssh-ed25519 AAAA...`). PuTTY `.ppk` format won't work.
- **Public key only in authorized_keys**: Never share private key (`-----BEGIN OPENSSH PRIVATE KEY-----`). Only the `.pub` content goes to server.
- **Key propagation delay**: GreenCloud requires **full VPS restart** (90-120s) after adding SSH key via panel before it works.
- **Three firewall layers**: UFW (internal) → aaPanel Firewall (app-level) → GreenCloud External Firewall (network-level). ALL must allow port 22.

### n8n Volume Migration & Recovery
When updating n8n via Docker and losing access to old workflows/users:
1. **Identify old volume**: `docker volume ls` → find anonymous volume (long hash name) created earlier
2. **Copy data to new volume**: `cp -r /var/lib/docker/volumes/OLD_VOLUME/_data/* /var/lib/docker/volumes/n8n_data/_data/`
3. **Fix permissions**: `chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data` (n8n runs as node/UID 1000)
4. **Copy encryption key**: `cp /var/lib/docker/volumes/OLD_VOLUME/_data/config /var/lib/docker/volumes/n8n_data/_data/config` — **critical for credential decryption**
5. **Restart container** with new volume mounted

### n8n User Recovery After Migration
If users disappear after volume migration (database reset):
1. Check old volume DB: `sqlite3 /var/lib/docker/volumes/OLD_VOLUME/_data/database.sqlite "SELECT id, email FROM user;"`
2. Copy user record to new volume:
   ```sql
   INSERT INTO user (id, email, createdAt, updatedAt, settings, disabled, mfaEnabled, roleSlug) 
   VALUES ('OLD_USER_ID', '', '', '', '{"userActivated":false}', 0, 0, 'global:owner');
   ```
3. Add auth_identity record for email login:
   ```sql
   INSERT INTO auth_identity (userId, providerId, providerType) VALUES ('OLD_USER_ID', 'OLD_USER_ID', 'email');
   ```
4. Restart n8n container

### WordPress FOUC Fix Pattern
For plugin pages showing layout shift before CSS loads:
```php
// In theme functions.php or mu-plugin
add_action('wp_head', 'fix_fouc', 1);
function fix_fouc() {
    if (is_page('TARGET_SLUG')) {
        echo '<style>body{opacity:0;visibility:hidden}</style>';
        echo '<script>document.addEventListener("DOMContentLoaded",()=>{document.body.style.opacity=1;document.body.style.visibility="visible"});setTimeout(()=>{document.body.style.opacity=1;document.body.style.visibility="visible"},3000)</script>';
    }
}
add_action('wp_enqueue_scripts', 'critical_css_inline', 1);
function critical_css_inline() {
    if (is_page('TARGET_SLUG')) {
        wp_add_inline_style('theme-main-style', '.plugin-selector{visibility:hidden}.loaded .plugin-selector{visibility:visible}');
    }
}
```

### aaPanel Terminal = Full Root Shell
No SSH needed for most ops:
- File Manager → Edit configs
- Terminal → Run commands as root
- Databases → phpMyAdmin/Adminer
- Logs → View error/access logs
- Services → Restart PHP/Nginx/OpenLiteSpeed
