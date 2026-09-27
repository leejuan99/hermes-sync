# Session Diagnostic Output Reference

Real output from a user session (Windows 10, 16GB RAM, Indonesian user) for comparison and pattern recognition.

## Startup Programs (Win32_StartupCommand)

```
Name                                                    Command
----                                                    -------
Ollama                                                  Ollama.lnk
OpenClaw Gateway                                        OpenClaw Gateway.cmd
Send to OneNote                                         Send to OneNote.lnk
OneDrive                                                "C:\Users\pc\AppData\Local\Microsoft\OneDrive\OneDrive.exe" ...
IDMan                                                   C:\Program Files (x86)\Internet Download Manager\IDMan.exe /...
kpm.exe                                                 "C:\Program Files (x86)\Kaspersky Lab\Kaspersky Password Man...
BraveSoftware Update                                    "C:\Users\pc\AppData\Local\BraveSoftware\Update\1.3.361.151\...
GoogleChromeAutoLaunch_17E89F440D584F67E92EAD2E51C3A3A4 "C:\Program Files\Google\Chrome\Application\chrome.exe" --no...
Opera Browser Assistant                                 C:\Users\pc\AppData\Local\Programs\Opera\assistant\browser_a...
SecurityHealth                                          %windir%\system32\SecurityHealthSystray.exe
Nearby Share                                            "C:\Program Files\Google\NearbyShare\nearby_share_launcher.e...
```

**Actionable:** Disable OneDrive, IDMan, kpm.exe, BraveSoftware Update, GoogleChromeAutoLaunch, Opera Browser Assistant, Nearby Share via Task Manager > Startup.

---

## Top Processes by CPU

```
ProcessName       Id        CPU  WorkingSet
-----------       --        ---  -----------
CapCut          3944 436.515625 -1022631936
kpm             8144 123.453125   206012416
Hermes         15244   120.3125   206041088
chrome          8040  79.046875   286408704
chrome          5196   62.53125   297816064
msedgewebview2  4988  50.265625   398233600
Hermes         16068   48.609375   105394176
chrome         17204      48.25   153546752
chrome         12560      45.25   199573504
python         10924         44   216965120
chrome         13620  42.765625   449146880
msedgewebview2 13648    37.5625   129855488
chrome         12012   33.40625   126894080
chrome         16988   25.15625   145682432
chrome         10060   23.71875   153845760
explorer       10700   23.15625   198496256
avpui           4660  22.609375    14159872
chrome          2220  22.546875   168603648
POWERPNT        3004  21.546875   193171456
chrome         12240  21.421875   170762240
```

**Key findings:**
- CapCut: ~436 CPU (highest), negative WorkingSet = reporting bug, actual ~3 GB
- kpm.exe: 123 CPU, 206 MB — Kaspersky Password Manager
- Hermes: 3 processes, ~500 MB total
- Chrome: 15+ processes, ~3 GB total
- msedgewebview2: 6 processes, ~1 GB total
- POWERPNT: 489 MB — PowerPoint open

---

## Top Processes by Memory (WorkingSet)

```
ProcessName        CPU        WorkingSet        PM
-----------        ---        ----------        --
Memory Compression            1450229760   3137536
chrome             42.65625    441409536 469667840
msedgewebview2     50.140625   395612160 442880000
avp                            340705280 633335808
chrome             62.40625    293490688 259117056
chrome             78.171875   282800128 306515968
kpm                119.0625    202334208 163074048
chrome             45.171875   199618560 319373312
Hermes             107.640625  196255744 294232064
explorer           22.1875     195715072 240791552
POWERPNT           21.40625    192516096 380829696
WhatsApp.Root      5.671875    187920384 124456960
chrome             21.328125   171446272 262799360
chrome             22.484375   169267200 249978880
chrome             23.40625    153968640 310820864
```

**Note:** Memory Compression (1.4 GB) is Windows memory management, not an app. Don't kill.

---

## Running Services (sc query) — Non-Microsoft Highlights

```
SERVICE_NAME: AdobeARMservice
DISPLAY_NAME: Adobe Acrobat Update Service
        STATE              : 4  RUNNING

SERVICE_NAME: AVP21.25
DISPLAY_NAME: Kaspersky Service 21.25
        STATE              : 4  RUNNING

SERVICE_NAME: ClickToRunSvc
DISPLAY_NAME: Microsoft Office Click-to-Run Service
        STATE              : 4  RUNNING

SERVICE_NAME: CoworkVMService
DISPLAY_NAME: Claude
        STATE              : 4  RUNNING

SERVICE_NAME: ksde.exe / ksdeui.exe
DISPLAY_NAME: Kaspersky components
        STATE              : 4  RUNNING

SERVICE_NAME: QuickShareService
DISPLAY_NAME: QuickShareService
        STATE              : 4  RUNNING

SERVICE_NAME: SamsungAccountService
DISPLAY_NAME: Samsung account
        STATE              : 1  STOPPED

SERVICE_NAME: VBoxGuest / VBoxService / VBoxMouse / VBoxSF / VBoxVideo / VBoxWddm
DISPLAY_NAME: VirtualBox services
        STATE              : 1  STOPPED
```

**Safe to set Manual/Disabled:** AdobeARMservice, ClickToRunSvc, CoworkVMService, QuickShareService, SamsungAccountService, VBox* services.

---

## Full tasklist (Key User Apps Only)

```
Image Name                     PID Session Name        Session#    Mem Usage
========================= ======== ================ =========== ============
CapCut.exe                    3944 Console                   12  2,980,908 K
CapCut.exe                   11572 Console                   12    136,596 K
CapCut.exe                   13632 Console                   12     59,504 K
CapCut.exe                   17384 Console                   12     63,332 K
CapCut.exe                    9064 Console                   12     73,344 K
CapCut.exe                   16624 Console                   12     60,648 K
CapCut.exe                    4568 Console                   12     60,872 K
Hermes.exe                   13148 Console                   12    116,304 K
Hermes.exe                   16068 Console                   12    104,112 K
Hermes.exe                    8252 Console                   12     44,728 K
Hermes.exe                   15244 Console                   12    225,196 K
Hermes.exe                    7908 Console                   12     79,904 K
chrome.exe                    8040 Console                   12    285,116 K
chrome.exe                   12560 Console                   12    207,360 K
chrome.exe                   13620 Console                   12    444,192 K
chrome.exe                   10060 Console                   12    184,088 K
chrome.exe                    5196 Console                   12    300,724 K
chrome.exe                   17204 Console                   12    151,420 K
... (15+ more chrome.exe)
msedgewebview2.exe            4988 Console                   12    453,848 K
msedgewebview2.exe           13648 Console                   12    167,580 K
msedgewebview2.exe           16848 Console                   12    134,096 K
msedgewebview2.exe            1744 Console                   12     10,304 K
msedgewebview2.exe             736 Console                   12     39,732 K
msedgewebview2.exe           11728 Console                   12     18,300 K
POWERPNT.EXE                  3004 Console                   12    489,104 K
kpm.exe                       8144 Console                   12    203,040 K
WhatsApp.Root.exe             8460 Console                   12    228,220 K
avp.exe                       3844 Services                   0    360,144 K
avp.exe                       6328 Services                   0     25,648 K
python.exe                   10924 Console                   12    222,744 K
python.exe                   15852 Console                   12     48,760 K
```

**CapCut total:** ~3.4 GB across 7 processes
**Chrome total:** ~3.5 GB across 20+ processes
**msedgewebview2 total:** ~1.1 GB across 6 processes
**Hermes total:** ~570 MB across 5 processes
**Kaspersky (avp + kpm):** ~585 MB

---

## User Actions Taken (Result)

1. `taskkill /f /im CapCut.exe` → freed ~3.4 GB
2. `taskkill /f /im chrome.exe` → freed ~3.5 GB (user reopened needed tabs)
3. Disabled kpm.exe, OneDrive, IDMan, Brave/Opera/Chrome auto-launch, Nearby Share via Task Manager > Startup
4. Set AdobeARMservice, ClickToRunSvc, CoworkVMService to Manual via services.msc

**Result:** User reported "ringan banget sekarang" (very light/fast now).