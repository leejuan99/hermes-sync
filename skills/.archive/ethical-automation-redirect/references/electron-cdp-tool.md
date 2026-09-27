# Electron + Playwright-CDP read-only tool blueprint

A working desktop-app pattern for a read-only browser research tool. Connects to
the user's already-open Edge/Chrome (CDP), reads results, exports CSV. No writes.

## File layout
```
app/
  package.json          # main: main.js; "start": "electron ."
  main.js               # Node side: window + IPC handlers + Playwright CDP
  preload.js            # contextBridge: exposes exactly the fns the UI calls
  renderer/
    index.html          # form (keyword, max, scroll) + log + results table
    renderer.js         # uses window.api.{run,exportCsv,onLog}
```

## package.json essentials
```json
{
  "main": "main.js",
  "scripts": { "start": "electron .", "dist": "electron-builder" },
  "dependencies": { "playwright": "^1.47.0" },
  "devDependencies": { "electron": "^31.0.0", "electron-builder": "^24.13.3" }
}
```

## Security wiring (do not skip)
- `webPreferences: { preload, contextIsolation: true, nodeIntegration: false }`.
- preload exposes a minimal surface only:
  ```js
  contextBridge.exposeInMainWorld("api", {
    run: (opts) => ipcRenderer.invoke("research:run", opts),
    exportCsv: (rows) => ipcRenderer.invoke("research:exportCsv", rows),
    onLog: (cb) => ipcRenderer.on("research:log", (_e, m) => cb(m)),
  });
  ```
- main registers matching `ipcMain.handle("research:run" / "research:exportCsv")`
  and pushes progress with `event.sender.send("research:log", msg)`.

## CDP connect (read-only core)
```js
const { chromium } = require("playwright");
const browser = await chromium.connectOverCDP("http://localhost:9222");
const context = browser.contexts()[0];          // reuse logged-in session
const page = await context.newPage();
await page.goto(searchUrl, { waitUntil: "domcontentloaded" });
// read-only: evaluate DOM + scroll. NEVER click Post / type into answer fields.
const items = await page.evaluate(() => /* collect anchors/cards */);
await page.mouse.wheel(0, 2200);                 // load more, human-ish delay
```
Dedupe by normalized text: `q.toLowerCase().replace(/\s+/g," ").trim()`.
CSV escape: wrap in quotes + double internal quotes if value matches `/[",\n]/`.

## Launch Edge in CDP mode (give the user these verbatim)
Windows (cmd):
```
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\EdgeDebugProfile"
```
Mac:
```
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --remote-debugging-port=9222 --user-data-dir="$HOME/EdgeDebugProfile"
```
Use a separate `--user-data-dir` so it doesn't clash with their main Edge.

## Playwright + CDP: skip the browser download
Because the tool uses `connectOverCDP` (attaches to the user's Edge), you do NOT
need `npx playwright install` browser binaries. That download is large and often
times out — and it's unnecessary here. Say so; don't make the user wait on it.

## Verification you CAN do (ad-hoc, headless)
- `node --check` every .js file.
- Run a temp script (`hermes-verify-*.js` under the OS temp dir) that asserts:
  pure helpers (csvEscape, dedupe), all files exist + parse, **preload surface
  matches every `window.api.*` call in renderer.js** (catches the classic
  Electron "undefined api method" bug), main registers the IPC channels the UI
  invokes, html wires renderer.js + has the control IDs.
- `npx electron --version` to confirm the binary resolves.

## Verification you CANNOT do (state honestly)
- Window actually opening — needs a display/desktop session; can't headless it.
- Live scrape against the platform — needs the user's logged-in Edge running;
  selector heuristics only prove out on a real run. Ask for sample live HTML to
  fix selectors when results come back empty.
