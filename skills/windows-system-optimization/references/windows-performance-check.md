# Windows Performance Quick Audit

Quick check sequence for this user's Windows 11 environment (`C:\Users\pc`, casual Indonesian, quick-action preference).

---

## 1. Top Resource Consumers
```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 ProcessName, CPU, WorkingSet
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 ProcessName, WorkingSet
```
Always report CapCut (~3 GB, 250+ CPU) first. It is the single biggest win.

## 2. Startup Audit
```cmd
wmic startup get caption,command,user /format:list
```
Safe to disable via `reg delete` (non-admin): Hermes_Gateway, OneDrive, IDMan, BraveSoftware Update, Opera Assistant, Chrome AutoLaunch, Nearby Share. Keep SecurityHealth (optional).

## 3. Service Audit (Admin Required)
```cmd
net session >nul 2>&1 || echo "NOT ADMIN"
sc query TabletInputService
```
Services that need admin (`sc config`): `TabletInputService`, `Fax`, `RemoteRegistry`, `WbioSrvc`, `icssvc`, Xbox services. `AdobeARMservice` and `ClickToRunSvc` should go to `demand` (not full disable).

## 4. Broken / Missing Drive
```cmd
wmic diskdrive get Model,Status,Size
Get-PhysicalDisk | Format-Table FriendlyName,OperationalStatus
```
If `Get-PhysicalDisk` only shows Samsung SSD and `wmic` shows `WDC WD10EZEX` with `Status: OK` but 0 partitions, and Device Manager shows `Unknown`, the drive is physically dead (`Event ID 51` in System logs). Capture the detection pattern, not the model as a permanent constraint.

## 5. Disk Space
```cmd
wmic logicaldisk get deviceid,size,freespace
```
250 GB SSD (`C:`) should keep ~15-20% free (37-50 GB). Current state: 67 GB free (~27%) — acceptable but tight.

## 6. Gateway / Telegram 24/7 Check
```bash
# SSH to VPS
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 'uptime'
# SSH executor
ssh -p 2222 -i ~/.ssh/vps_key root@194.127.192.52 'netstat -tlnp | grep 5679'
# Webhook (independent)
curl -s -X POST https://n8n.smartmillionaire.co.id/webhook/telegram/webhook -H 'Content-Type: application/json' -d '{"message":{"message_id":1,"text":"/status"}}'
```
If `netstat` shows `LISTEN` but Telegram still does not reply: check gateway service (`sc query hermes-gateway`) and gateway config (`Telegram disabled`).
