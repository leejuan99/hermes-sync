---
name: windows-performance-optimization
description: Diagnose and optimize Windows performance by checking startup programs, running processes, services, and memory/CPU hogs. Provides actionable recommendations to disable unnecessary apps and services.
category: software-development
tags: [windows, performance, optimization, diagnostics, system-admin, troubleshooting]
---

# Windows Performance Optimization

## When to Use
- User reports "Windows lambat" / "PC slow" / "lag"
- High RAM/CPU usage with unknown cause
- Want to debloat startup and background services
- Regular maintenance / spring cleaning

## Diagnostic Commands (Run in Order)

### 1. Startup Programs
```powershell
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location, User | Format-Table -AutoSize
```
Check Task Manager > Startup tab for GUI-friendly disable.

### 2. Top Processes by CPU
```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 20 Id, ProcessName, CPU, WorkingSet | Format-Table -AutoSize
```

### 3. Top Processes by Memory (Working Set)
```powershell
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 20 Id, ProcessName, CPU, WorkingSet, PM | Format-Table -AutoSize
```

### 4. Non-Microsoft Services Running
```cmd
sc query type= service state= all | findstr "RUNNING"
```
Then filter out Microsoft/Windows/System services manually or via:
```powershell
Get-Service | Where-Object {$_.Status -eq 'Running' -and $_.StartType -eq 'Automatic' -and $_.Name -notmatch '^(Microsoft|Windows|WinHttp|Wmi|Wlan|Wwan|W32Time|Wdi|Wbengine|Wcmsvc|Wdnisvc|Wbiosrvc|Wlidsvc|Wlpasvc|Wmansvc|WmiApSrv|WSearch|Wuauserv|WwanSvc|XblAuthManager|XblGameSave|XboxGipSvc|XboxNetApiSvc)'} | Select-Object Name, DisplayName, Status, StartType | Format-Table -AutoSize
```

### 5. Full Tasklist (Cross-check)
```cmd
tasklist /FO TABLE
```

## Common Bloatware to Disable (Indonesian Context)

| App/Service | Typical RAM | Action |
|-------------|-------------|--------|
| CapCut / video editors | 2-4 GB | **Tutup kalo lg ga dipake** |
| Chrome/Edge (many tabs) | 2-5 GB | Restart browser, tutup tab |
| msedgewebview2 | 500 MB-1 GB | Normal kalau pakai Electron/Edge apps |
| Kaspersky (avp.exe, kpm.exe) | 400-600 MB | Biarkan AV, matiin Password Manager (kpm) kalo ga dipake |
| OneDrive | 100-200 MB | Disable startup kalo ga sync |
| IDM (IDMan.exe) | 50-100 MB | Disable startup |
| Browser auto-launchers | 50-200 MB each | Disable di Task Manager > Startup |
| Nearby Share / Quick Share | 50-100 MB | Disable kalo ga transfer HP↔PC |
| Opera/Brave/Chrome updaters | 20-50 MB each | Disable startup |
| Adobe/Office updaters | 50-150 MB | Set ke **Manual** di services.msc |

## Services Safe to Set Manual/Disabled

| Service Name | Display Name | Safe To Disable? |
|--------------|--------------|------------------|
| AdobeARMservice | Adobe Acrobat Update | ✅ **Manual** |
| ClickToRunSvc | Office Click-to-Run | ✅ **Manual** |
| AdobeCollabSync | Adobe Collab Sync | ✅ **Disabled** |
| QuickShareService | Quick Share | ✅ **Disabled** kalo ga dipake |
| SamsungAccountService | Samsung Account | ✅ **Disabled** |
| VBoxGuest/VBoxService | VirtualBox | ✅ **Disabled** kalo ga VM |
| CoworkVMService | Claude Desktop | ✅ **Manual** kalo ga pakai |

## Quick Win Commands (Run as Admin)

```cmd
REM 1. Kill biggest RAM hogs instantly
taskkill /f /im CapCut.exe
taskkill /f /im chrome.exe

REM 2. Disable startup items (requires reboot)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OneDrive" /f /d ""
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "IDMan" /f /d ""

REM 3. Set services to Manual
sc config AdobeARMservice start= demand
sc config ClickToRunSvc start= demand
sc config CoworkVMService start= demand
```

## Communication Style (User Preference)
- **Bahasa Indonesia informal** — gunakan "gua/lu", "bray", "gass", "susah njir"
- **Prioritaskan GUI** — arahkan ke Task Manager > Startup / Services.msc bukan cuma CLI
- **Actionable tables** — format markdown dengan kolom: App, RAM, Action
- **Urgent first** — urutkan dari paling boros RAM/CPU ke paling kecil
- **Jelaskan "kenapa"** — user mau tau alasannya, bukan cuma daftar perintah

## Pitfalls to Avoid
- ❌ Jangan disable Microsoft Defender / Windows Security services
- ❌ Jangan disable `WinDefend`, `WscSvc`, `BFE`, `Dhcp`, `Dnscache`, `EventLog`, `PlugPlay`, `RpcSs`, `Schedule`, `Winmgmt`, `WudfSvc`
- ❌ Jangan disable AV services (Kaspersky `AVP21.25`, etc) kecuali user minta ganti AV
- ❌ Jangan hapus registry keys manual kecuali benar-benar yakin — pakai Task Manager > Startup tab
- ⚠️ CapCut sering muncul banyak proses (CapCut.exe + 5-6 CapCut.exe child) — kill semua
- ⚠️ Chrome/Edge pakai multiprocess — lihat **total** WorkingSet, bukan per-PID
- ⚠️ `msedgewebview2` dipakai Hermes, Teams, Outlook, Widgets — jangan kill sembarangan

## Verification Steps
1. Re-run memory check after cleanup: `Get-Process | Sort WorkingSet -Desc | Select -First 10`
2. Check boot time: `systeminfo | findstr "Boot Time"`
3. User feedback: "gimana sekarang? lebih ringan?"