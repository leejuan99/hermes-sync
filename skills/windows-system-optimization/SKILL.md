---
name: windows-system-optimization
description: "Windows PC performance audit: startup disable, service disable, process cleanup, disk/hardware check, gateway/VPS status verification. For this user's Windows 11 + GreenCloud VPS + Hermes environment."
version: 1.0.0
category: software-development
tags: [windows, performance, startup, services, disk, gateway, vps]
---

# Windows System Optimization Skill

Use when the user asks about Windows being slow, asks to disable unneeded apps/services, or reports broken/missing drives. The user runs Windows 11 (`C:\Users\pc`), uses casual Indonesian (`bray`, `gass`), prefers visual paths but accepts CLI commands, and expects quick action over long explanation.

## Trigger Conditions
- User asks about Windows slowness (`"cek windows", "ada yang bikin lambat gak"`)
- User asks to disable/remove applications (`"open claw gateway bisa lo delete?"`)
- User reports a drive missing (`"Drive D gak kebaca"`)
- User mentions Telegram/gateway not responding (`"telegram gak bales"`)

## User Preferences (Always-On Rules)
- **Quick action over explanation:** Provide exact command/path; add brief note only when asked.
- **GUI preferred but CLI given:** When a web panel exists (aaPanel, Task Manager), mention it first; fall back to CLI.
- **Casual register:** Respond in the same register (`lo`, `gua`, `bray`, `gass`, `susah njir`).
- **No fabricated output:** If a command fails, report the real error (`Access is denied`, `Unknown device`, `timeout`).
- **Security awareness:** The user previously shared a private SSH key in chat (`vps_key`). The agent must remind about rotation/security when SSH keys are mentioned.

## Procedure

### 1. Identify Resource Hogs (Always Start Here)
```powershell
# Top CPU consumers
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 ProcessName, CPU, WorkingSet

# Top memory consumers
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 ProcessName, WorkingSet

# Startup items
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, User
```
**Pitfalls:**
- **CapCut (`CapCut.exe`)** consumes ~3 GB RAM and 250+ CPU. Always recommend closing it first — it is the single biggest performance win.
- **Multiple Chrome processes** (`chrome.exe`, `msedgewebview2.exe`) accumulate to ~3 GB+. Restart Chrome (kill all processes, reopen) rather than just closing tabs.
- **Python background scripts** (`python.exe`, `pythonw.exe`) may run unnoticed. Check with `tasklist` before assuming they are needed.

### 2. Clean Startup (Non-Admin Registry Deletions)
```cmd
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Hermes_Gateway" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OneDrive" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "IDMan" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "BraveSoftware Update" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "kpm" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Opera Browser Assistant" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "GoogleChromeAutoLaunch_..." /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Nearby Share" /f
```
**Pitfall:** Removing `Hermes_Gateway` from startup stops the gateway from auto-starting. If the user expects Telegram/gateway 24/7 operation, the gateway must either be restored (add back) or deployed to the VPS — not just disabled.

### 3. Service Disable (Requires Admin — `.bat` File Pattern)
The `.bat` file `disable-useless-services.bat` (Desktop) checks for admin. Running it without admin shows `[ERROR] Butuh Administrator!`.

**Always verify admin before attempting `sc config`:**
```cmd
net session >nul 2>&1
```
If it fails (`Access is denied`), the `.bat` will block execution.

**Commands that require admin (`sc config`):**
```cmd
sc config TabletInputService start= disabled && sc stop TabletInputService
sc config Fax start= disabled
sc config RemoteRegistry start= disabled
sc config WbioSrvc start= disabled
sc config icssvc start= disabled
sc config XboxGipSvc start= disabled
sc config XboxNetApiSvc start= disabled
sc config XblAuthManager start= disabled
sc config XblGameSave start= disabled
sc config AdobeARMservice start= demand
sc config ClickToRunSvc start= demand
```
**Pitfalls:**
- `sc config` requires admin (`FAILED 5` = Access Denied). A user saying "kerjakan" does not grant admin — the `.bat` must be run with `Run as administrator`.
- `TabletInputService` saves ~63 MB RAM but removes touch/pen/handwriting input. Only disable if no touchscreen/stylus is used.
- `AdobeARMservice` / `ClickToRunSvc` should be set to `demand` (manual), not fully disabled, so Office updates still work.
- **Never disable `avp.exe` (Kaspersky AV)** or `wscsvc` (Windows Security Center)** — these are security-critical.

### 4. Broken / Missing Drive Check
```cmd
wmic diskdrive get Model,Status,Size
Get-PhysicalDisk | Format-Table FriendlyName,Size,OperationalStatus,HealthStatus
Get-Partition | Format-Table DiskNumber,DriveLetter,Size,Type
```
**Pitfalls:**
- **WDC WD10EZEX-00BN5A0 (1 TB)** was detected as `Unknown` with `Status: Unknown` (`Get-PnpDevice`). `wmic diskdrive` showed only the Samsung SSD (250GB) and the WDC with 0 partitions.
- **Event Log ID 51** (`"An error was detected on device \Device\Harddisk1\DR1 during a paging operation"`) confirms bad sectors / physical failure. The drive is broken, not just unmounted.
- **Do NOT write failed drives as a durable skill rule** — this is an environment failure. Capture the detection pattern (`EventLog` ID 51 + `Unknown` PnP status + missing partition + `netstat` / `diskpart` absence) but do not state "WD 1TB is broken" as a permanent constraint. The fix is clone/recover (`Rescuezilla`, `ddrescue`) or replace; document only the detection method.

### 5. Disk Space Audit
```cmd
wmic logicaldisk get deviceid,size,freespace
```
For a 250 GB SSD (Samsung 860 EVO): ~67 GB free (~27%) is acceptable but tight. Ideal minimum: 15-20% free (37-50 GB free). If below that, clean `/tmp`, `C:\Users\pc\AppData\Local\Temp`, and old logs.

### 6. Gateway / Telegram 24/7 Architecture Check
From the session reference (`request_dump_20260810_235535_7b6329`):
- The gateway architecture requires an SSH executor (`/root/ssh_executor.py` on VPS, port 5679) and a webhook endpoint (`n8n.smartmillionaire.co.id/webhook/telegram/webhook`).
- The bot (`@hermesLJ99Bot`) sends via Telegram API; n8n handles the webhook relay.
- If Telegram stops responding, verify independently of the gateway:
  1. SSH access: `ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 'uptime'`
  2. SSH executor LISTENING: `netstat -tlnp | grep 5679`
  3. Webhook responds: `curl -X POST ...`
  4. Gateway service: `sc query hermes-gateway` / `systemctl status hermes-gateway`
- **Pitfall — User expects 24/7 via VPS:** A user stating "Telegram should connect to VPS 24 hours" indicates the architecture assumption is VPS-hosted gateway, not local PC. Confirm deployment before diagnosing.

## References
- `references/windows-performance-check.md` — Quick audit commands (top CPU/memory, disk, startup)
- `references/gateway-24-7-deployment.md` — SSH executor, webhook verification, gateway service checks (see `vps-server-management`)

## Scripts
- `scripts/check-startup.bat` — List and disable startup entries (non-admin registry deletes for user-level items)
- `scripts/disable-services.bat` — Admin `.bat` for `sc config` service disable (requires `Run as administrator`)
- `scripts/reset-wd1tb.ps1` — PowerShell to disable/re-enable PnP device for dead drive (admin only; may fail with generic error if device is physically dead)

## Common Pitfalls (Always Active)
- **CapCut is the #1 RAM/CPU hog** (~3 GB RAM, 250+ CPU). Always check and recommend closing first.
- **Chrome accumulates processes** (20+ instances). Restart kills all; closing tabs one-by-one does not reclaim memory fully.
- **SSH timeout (`exit 124`) is not unreachable** — confirm with `ping` before diagnosing gateway failure.
- **SSH executor (`port 5679`) is independent of gateway startup** — check `netstat` separately.
- **`sc config` requires admin** (`FAILED 5`). A `.bat` that does not verify admin will fail silently or block. Always include admin check (`net session >nul 2>&1`) in automation scripts.
- **Broken drive (`Unknown` PnP + Event 51) is a hardware failure, not a mount issue.** The durable rule is the detection pattern, not the drive model.
- **User's VPS expectation**: When the user expects 24/7 gateway operation, confirm VPS deployment (`netstat | grep 5679` remotely) rather than only restoring local startup.
