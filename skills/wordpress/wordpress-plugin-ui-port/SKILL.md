---
name: wordpress-plugin-ui-port
description: "Use when porting a design into a WordPress plugin UI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wordpress, plugin, ui, design-port, reskin, templates]
    related_skills: [sejoli, requesting-code-review]
---

# WordPress plugin UI port (design prototype → plugin templates)

Re-skin an existing WordPress plugin to match a design prototype — a React/Tailwind demo, a mockup, another product's look — without touching the engine behind it. Output: PHP templates + one CSS file + vanilla JS, verified and packaged as an installable zip.

## When to Use

- "Tiru tampilannya" / "make this plugin look like <prototype>" — restyle requests for a plugin the user runs.
- Porting a prototype you were handed (zip / URL / screenshots) into an existing plugin's pages.
- Any redesign where server-rendered PHP and theme/Elementor pages rule out a JS build step.

## Procedure

1. **Read the prototype; extract tokens.** Unzip/read its source (components + global CSS, e.g. `App.tsx`, `index.css`) or crawl the live pages. Write down: palette hexes, radii, shadow levels, spacing, badge/chip shapes, and the exact label copy — the copy is part of the design when the user says "tiru persis".
2. **Enumerate the contract you must NOT break, before restyling.** Every AJAX endpoint, action name, nonce, request field and response shape, plus each template's PHP variables. A re-skin changes markup/CSS/JS only.
3. **Re-build in three layers, no bundler:**
   - PHP templates for structure (server-rendered); JS contract data lives in `data-*` attributes (`data-<pfx>-add`, `data-pid`, `data-unit`, `data-value` for raw numbers).
   - One CSS file built on custom properties (color/radius/shadow vars) scoped under a wrapper class, with tint scales (`--p-50/-100/-200`) so one override re-themes everything.
   - Vanilla JS with event delegation on `document` (handlers survive AJAX-replaced markup) and one `post(action, data)` helper that picks the right nonce per action.
4. **Verify with scripted gates** (deterministic, seconds each):
   - Syntax: `node --check <file>.js`.
   - PHP lint on a COPY of the touched files (server `/tmp` copy, or a local PHP matching prod) — never lint by overwriting the installed plugin.
   - Selector contract: `scripts/selector-contract.sh data-<pfx> assets/js/<file>.js templates includes` — every `data-*` selector the JS references must be emitted by server markup; anything JS creates itself will show as advisory, everything expected from templates must match.
   - Numeric round-trip: any number JS reads (line totals, qty) must come from a `data-` attribute, not parsed out of formatted text (`Rp 1.234.567`) — text parsing breaks on every format change.
5. **Prefer server-rendered re-fragments for money math**: add a "give me the fresh fragment" AJAX endpoint (rendered HTML + totals) instead of recomputing prices in JS.
6. **Bump the asset version constant** (the plugin's version define used at enqueue time) whenever CSS/JS change, or browsers serve the stale skin.
7. **Package from git:** `git archive --format=zip --prefix=<slug>/ -o <output>.zip HEAD` → single top folder, no `.git`; verify the listing (top folder name, templates present) before handover.
8. **Deliver GUI-first:** zip path + wp-admin steps (Plugins → Add New → Upload Plugin → "Replace current with uploaded" → Ctrl+F5). This user prefers GUI flows over SSH/SCP; never deploy to a production server without an explicit go-ahead. List anything NOT ported and why (missing source data, unbuilt engine features) — do not fake data in the UI. **Deploy cadence once the user is iterating on live:** a build the user has NOT yet installed ships as a ZIP only; once they installed a version themselves and report bugs from the live site, ship each fix to that same install — announce every redeploy, and keep a per-version ZIP + git commit so rollback is one file (offer it when announcing).

## Pitfalls

- **Full-file rewrites and the write_file guard:** `write_file` refuses to overwrite a file unless it was freshly fully read in the same task, and even a re-read can be refused as "partial view". For whole-file rewrites, either `patch` with the file's complete current content as `old_string`, or `rm` the file via terminal first and write it as a new file. Pick one path immediately — repeated re-reads waste turns.
- **Don't "clean up" the data protocol while re-skinning.** Keep endpoint/nonce/response contracts byte-identical; the tested engine (orders, payments, commissions) breaks silently behind an OK-looking UI.
- **`innerHTML`-injected `<script>` never executes** and stale element references die — after AJAX re-renders rely on delegated listeners; if injected HTML must run JS, echo it server-side instead.
- **Prototype features with no backing data are skipped and named**, never invented (no rating stars when the system stores no ratings; no strikethrough price when only one price exists).
- **`[hidden]` loses to author `display:` rules — always ship `.pfx [hidden] { display: none !important; }` with component styles.** A `display:flex/grid` on a modal, drawer, summary row or footer silently defeats the HTML `hidden` attribute (author rules beat UA rules), so a "hidden" empty modal covers the whole page and collapse-toggles never collapse. One explicit rule fixes the whole family, and it is the first thing to grep for when a live user reports "modal/panel always visible".
- **Money math is server-side, always.** Every mutation response should carry a `lines` map of pre-formatted totals; JS only assigns those strings and reads numbers from `data-*` attributes only. Symptom of violating this: qty +1 turned a line total into `Rp 4.326.220.000.002.000.000` because text parsing swallowed digits out of the product title ("Batch 16-31").
- **Shortcode-only widgets are invisible widgets.** A floating cart/review/footer bar rendered only where its shortcode is pasted will be "missing" on every other page — auto-inject from `wp_footer` (guard `is_admin()`, own routes, and a rendered-once flag) instead of hoping the user edits pages.
- **Resolve option values by type before using them as URLs.** Plugin options (e.g. Sejoli logo) often store attachment IDs — a bare `"3345"` in `src` renders a broken-image icon; convert numeric → `wp_get_attachment_image_url()`, and run `set_url_scheme()` / force https on anything that may be `http://` (mixed-content blocking hides payment/bank logos on HTTPS pages).
- **Grids must key off container width, not viewport width.** Theme member-area layouts can give a ~630px content column on a 1250px screen; `repeat(auto-fill, minmax(230px, 1fr))` adapts, a `@media (min-width: 1100px)` column override does not.
- **Guard template array keys with `isset()`** when pulling from engine data objects (e.g. cart line `type` may not exist) — undefined-key warnings print into HTML on production.
- **Strip prototype dev-isms before shipping.** "Route: /checkout", "Intercept", stack notes were fine in the design demo and read as bugs on a real customer checkout — replace with customer copy while keeping the visual chip.
- **Verify the LIVE page, not your own templates.** The loop that caught every bug above: headless load of the real URL + `Page.addScriptToEvaluateOnNewDocument` error collector (read `window.__smcErr` after load) + DOM/computed-style asserts (modal `display === 'none'`? drawer element exists? line total equals the server-formatted string?) + one `capture_screenshot()` read back by a vision model. Do this before declaring any re-skin done, and re-run it as the regression pass after fixes.
- **Design interactions for a SLOW host: optimistic UI + per-item serial queue.** Shared-hosting admin-ajax can take seconds per round trip; when a stepper only changes after the server re-render, users read it as broken ("quantity doesn't increase") and clicks issued mid-refresh land on replaced DOM. Ship: instant local update from `data-*` values + a per-product update queue that debounces (~90 ms) and coalesces rapid clicks into ONE request (last value wins), reconciled by the response. Recipe: `references/interaction-patterns.md`.
- **Every mutable number carries a `data-value` that every response refreshes.** Optimistic math reads its base from `data-value`; a template or handler that writes only `textContent` leaves a stale base (first click appears to do nothing, the next jumps to a wrong amount). Both the server render AND every AJAX handler response must write the attribute.
- **Instrument AJAX by wrapping `window.fetch`, injected ONCE per browser session (guard with a window flag).** CDP `addScriptToEvaluateOnNewDocument` accumulates across calls and re-runs on every navigation, so stacked wrappers duplicate log entries and fabricate "double request" bugs. Before believing a duplicated handler, count the page's script tags for your file; and read instrumentation only AFTER latency settles — pre-settle reads report false states.
- **Guard the JS entry point against double-binding** (`if (window.__pfxInit) return; window.__pfxInit = true;`) — cheap insurance against double enqueues / theme copies silently doubling every click.
- **Match verification depth to risk:** for UI-only changes the scripted gates above ARE the verification; reserve the one independent reviewer subagent pass for changes touching money, auth, or data integrity (see `requesting-code-review`).

## References

- `references/interaction-patterns.md` — slow-host interaction patterns (optimistic qty + coalescing queue + `data-value` money protocol) and the headless-browser instrumentation/verification recipe.
- Worked example with project-specific lint/package commands: the `sejoli` skill's multicart-addon reference notes (Sejoli MultiCart storefront/drawer/checkout port).
- `scripts/selector-contract.sh` — the `data-*` selector gate (exit 1 lists selectors JS expects but templates never emit).
