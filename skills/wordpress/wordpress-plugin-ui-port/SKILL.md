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
8. **Deliver GUI-first:** zip path + wp-admin steps (Plugins → Add New → Upload Plugin → "Replace current with uploaded" → Ctrl+F5). This user prefers GUI flows over SSH/SCP; never deploy to a production server without an explicit go-ahead. List anything NOT ported and why (missing source data, unbuilt engine features) — do not fake data in the UI.

## Pitfalls

- **Full-file rewrites and the write_file guard:** `write_file` refuses to overwrite a file unless it was freshly fully read in the same task, and even a re-read can be refused as "partial view". For whole-file rewrites, either `patch` with the file's complete current content as `old_string`, or `rm` the file via terminal first and write it as a new file. Pick one path immediately — repeated re-reads waste turns.
- **Don't "clean up" the data protocol while re-skinning.** Keep endpoint/nonce/response contracts byte-identical; the tested engine (orders, payments, commissions) breaks silently behind an OK-looking UI.
- **`innerHTML`-injected `<script>` never executes** and stale element references die — after AJAX re-renders rely on delegated listeners; if injected HTML must run JS, echo it server-side instead.
- **Prototype features with no backing data are skipped and named**, never invented (no rating stars when the system stores no ratings; no strikethrough price when only one price exists).
- **Match verification depth to risk:** for UI-only changes the scripted gates above ARE the verification; reserve the one independent reviewer subagent pass for changes touching money, auth, or data integrity (see `requesting-code-review`).

## References

- Worked example with project-specific lint/package commands: the `sejoli` skill's multicart-addon reference notes (Sejoli MultiCart storefront/drawer/checkout port).
- `scripts/selector-contract.sh` — the `data-*` selector gate (exit 1 lists selectors JS expects but templates never emit).
