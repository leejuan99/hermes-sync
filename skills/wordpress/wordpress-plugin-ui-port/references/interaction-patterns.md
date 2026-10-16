# Interaction patterns for slow hosts (and how to verify them)

For plugin UIs that talk to admin-ajax on shared hosting: round trips take 0.5–4 s, so any control whose visible state only changes after a server re-render reads as BROKEN to real users ("the quantity doesn't increase", "the button does nothing"). Two patterns fix the whole class, plus the verification recipe that proves it live.

## 1. The `data-value` money protocol

Hard rules — each exists because breaking it produced a real, user-visible bug:

- Raw numbers live in attributes, never parsed from formatted text (`data-unit` on line rows, `data-value` on line totals / subtotals / grand totals).
- **Every** server render AND **every** AJAX handler response writes `data-value` alongside the text. A template that renders only text (and a handler that updates only `textContent`) leaves a stale base — symptom: subtotal appears frozen on the first click and jumps to a wrong amount on the next.
- Server response shape: a `lines` map `{pid: {quantity, subtotal, subtotal_formatted}}` per mutation makes every UI surface (drawer, cart page, checkout summary) reconcilable without JS money math. Formatted strings come from the server formatter; JS only assigns them.

## 2. Optimistic qty + per-item serial queue

Goal: the number moves INSTANTLY on click; the server reconciles a moment later; rapid clicks never lose or replay a quantity.

```js
var qtyQueues = {};

function queueCartUpdate(pid, qty) {
    var q = qtyQueues[pid] || (qtyQueues[pid] = { target: qty, running: false, scheduled: false });
    q.target = qty;                                   // last value always wins
    if (q.running || q.scheduled) { return; }

    q.scheduled = true;
    window.setTimeout(function () {                   // ~90 ms debounce: a click
        q.scheduled = false;                          // burst = ONE request
        if (q.running) { return; }
        q.running = true;
        (function flush() {
            var target = q.target;
            post('update', { product_id: pid, quantity: target }).then(function (res) {
                q.running = false;
                if (!res || !res.valid) { reconcile(); return; }
                applyServerTotals(res);               // counts + data-values
                if (q.target !== target) { q.running = true; flush(); return; }
                reconcile();                          // re-render fragments
            });
        })();
    }, 90);
}
```

Wiring (+/− buttons, typed values): compute `oldQty` from the CURRENT input value at click time; set every same-product input to `newQty` optimistically; update line totals absolutely (`unit × qty`); apply the subtotal/total delta to each surface's `data-value` base; then queue. Store the pre-edit value on `focusin` (attribute `data-prev`) so typed changes compute the right delta — do NOT rely on synthetic `change` events dispatched from click handlers.

Do NOT disable steppers during flight: serialization + coalescing already prevents lost/duplicated updates, and disabled controls make a slow host feel slower.

## 3. Reveal animations in background tabs

`requestAnimationFrame` is throttled/paused in background and headless tabs, so a class-based slide-in never starts. Pair it: `requestAnimationFrame(reveal); setTimeout(reveal, 60);` — idempotent, works in both worlds.

## 4. Live verification recipe (headless browser)

1. **Error collector** — inject once per session:
   `cdp('Page.addScriptToEvaluateOnNewDocument', source=...)` with `window.__err=[]` + `window.addEventListener('error', …)` + `unhandledrejection`; read `window.__err` after load and after interactions. Expect `[]` as the pass condition.
2. **AJAX instrumentation** — same injection mechanism, wrap `window.fetch` to log `{action, product_id, quantity, status}`. **Guard the injection with a window flag and inject only ONCE**: `addScriptToEvaluateOnNewDocument` accumulates across calls and re-runs every script on each navigation, so repeated injections stack wrappers, duplicate log entries, and fabricate "double request" bugs. Sanity checks: count `script[src*=your.js]` tags before suspecting duplicate handlers; filter the log by action name.
3. **Assert after settle, not instantly** — a mutation chain is click → update request → reconcile request → DOM swap; on slow hosts that is seconds. Poll until stable (or wait generously) before reading values, or you will report false negatives/positives ("drawer empty / not open" while its refresh was still in flight).
4. **Structured asserts, not vibes**: computed `display` of what should be hidden, element existence, input values, line total == server-formatted string, `data-value` == expected number, fetch log entries. Then one `capture_screenshot()` read back by a vision model to catch what DOM asserts cannot (empty panels, broken logos, dev-jargon copy).
5. **Debug checklist for "the click does nothing"**: (a) netlog — did a request fire at all? (b) after settle — what does the DOM show? (c) handler binding — double-init guard present, script loaded once? (d) markup contract — the selector-contract gate; (e) server response `valid` flag true?
