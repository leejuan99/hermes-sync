---
name: smart-binary-mlm
description: "Use when working on the Smart Binary MLM plugin."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [mlm, binary, wordpress, sejoli, commissions]
metadata:
  hermes:
    tags: [mlm, binary, wordpress, sejoli, commissions]
    related_skills: [wordpress-mcp-integration, subagent-fanout, novamira-mcp-troubleshooting]
---

# Smart Binary MLM plugin (member.smartmillionaire.co.id)

## When to Use

Any task touching the smart-binary MLM plugin or the member site's MLM/commission/admin code: bug fixing, bonus/commission configuration, payout logic, admin UI changes, MCP access, audits.

Custom WordPress binary-plan MLM plugin "smart-binary" on the PRODUCTION membership site member.smartmillionaire.co.id — real members and real IDR commissions/payouts (~3,400 members).

## Site & access

- Separate WP install from smartmillionaire.co.id (own DB, own credentials). Admin: leejuan (ID 1). DB prefix `wplo_`. Plugin dir: `/www/wwwroot/member.smartmillionaire.co.id/wp-content/plugins/smart-binary`.
- VPS: `ssh -i ~/.ssh/vps_key -p 2222 -o StrictHostKeyChecking=no root@194.127.192.52`. WP-CLI: `cd /www/wwwroot/member.smartmillionaire.co.id && wp ... --allow-root`.
- MCP: server `novamira-member` (npx @automattic/mcp-wordpress-remote, WP_API_URL=https://member.smartmillionaire.co.id/wp-json/mcp/novamira, user leejuan, app password generated via WP-CLI `wp user application-password create`). Tools load after `/reload-mcp` or a new session.
- BEFORE any production FILE edit: `tar czf /www/wwwroot/backups/smart-binary-<tag>-$(date +%Y%m%d%H%M).tar.gz smart-binary` from the plugins dir.
- BEFORE any destructive DB op (wipe / reset / rebuild): `wp db export /www/wwwroot/backups/member-db-<label>.sql --allow-root` FIRST (DB `thegamec_wp632`, full dump ≈193 MB) — a plugin-dir tar does NOT restore data, that dump is the only undo.

## Architecture map

- Point-based commission, NO BV (v1.0.0). Packages Starter/Pro/Elite. Tables `{prefix}sb_*` (~29).
- `includes/core/`: sb-member (placement, activation, triple-bundle), sb-tree (binary legs, BV propagation, foundation leg), sb-period, sb-point-system (leg points per YYYY-MM period), sb-wallet, sb-payout, sb-currency, sb-rank, sb-package, sb-subscription.
- `includes/bonuses/`: one class per bonus type + engine + base (pairing, sponsor, level, matching, pool, teampool, royalty, faststart, ROB, leadership, shared milestone, rank achievement, subscription shield, level pairing).
- `includes/integrations/`: **Sejoli = the LIVE store path**; WooCommerce & FluentCart = on hold.
- `includes/notifications/`: email/telegram/whatsapp senders, templates, logs.
- `includes/class-sb-rest.php` (~1,300 lines): Vue admin SPA API under /mlm/v1, all routes gated by `current_user_can('manage_options')`.
- `admin/`: PHP page partials + Vue app.js (~1,500 lines). `public/`: member dashboards, shortcodes, webinar room.
- Binary Tree view = the SPA `Tree` component in `admin/js/app.js`, rendering `#mlm-tree-canvas` with its OWN renderer (`.tx-tree` / `.tx-node` / `.tx-card` + jQuery) — NOT D3 (D3 is only the dashboard chart). Depth is the REST `levels` param in `class-sb-rest.php` (shipped default 5, cap 8) and the app.js dropdown + `levels:` default mirror it. PITFALL: a tall multi-HU spine (e.g. 7 HU levels before the first member) puts ALL member data past the default depth, so the tree renders EMPTY ('data gak tampil') even though the API returns the data — the fix is to raise the API cap + default AND the app.js `levels:` default + dropdown, then confirm members show at the DEFAULT view, not only when the level selector is maxed. Before blaming a redesign, diff the component against the pre-change backup: the tree code is often byte-identical, and the real cause is depth/cache.

SECOND cause of the same symptom (confirmed): `_markDefaultCollapse(node, depth)` auto-collapses EVERY node at `depth>=1`, so the canvas shows only the root plus its two immediate children (the empty leg painted as an 'Empty Slot' card) and the owner reports 'data gak tampil' even though the API payload and the Tree component are both correct. A reportedly-broken tree that RENDERS 2 nodes is this collapse, not a bug. Fix BOTH halves: raise the API `levels` cap/default + the app.js dropdown/default, AND raise the auto-collapse threshold (e.g. to `depth>=8`) so the whole HU spine is expanded at the DEFAULT view. Related gotcha: the `levels:` default MUST be a value present in the dropdown options array (a default of 8 with options `[3,5,7,10,15,20]` renders the `<select>` BLANK). When the owner says the tree is empty, ask for a SCREENSHOT before editing production code — the rendered page (2 cards + 'Empty Slot') identifies the cause instantly and avoids a second blind fix.

## Finding things on this site (greps lie here)

- **Hooks are registered in loops with concatenated names, so grepping the composed hook returns nothing.** `includes/class-sb-core.php` wires AJAX as `'wp_ajax_sb_' . $name` / `'wp_ajax_nopriv_sb_' . $name` (and the `mlm_` twins) over name→method arrays (admin list, member list, a `[ 'register_submit', 'search_sponsor' ]` public list, a webinar list). `grep -rn 'wp_ajax_nopriv_sb_search_sponsor'` finds ZERO hits while that hook is live. Always confirm a hook by reading the loop arrays and grepping the bare `$name`; treat an empty grep as "the name is composed", never as "it does not exist" — this is exactly how a real audit finding gets misread as an auditor hallucination.
- **Admin menus / shortcodes / AJAX handlers can come from the sandbox, not the plugin.** The top-level `🎯 SM Coach` menu lived only in `wp-content/novamira-sandbox/smart-millionaire-coach.php`, which registers it as a SUBMENU of `smart-binary` when that parent is already in `$menu`, otherwise as a TOP-LEVEL `add_menu_page`. Grep of `plugins/`, `themes/` and `mu-plugins/` for the label or slug returns nothing — dump the registered menus instead (recipe in the `novamira-mcp-troubleshooting` skill) and grep the flat sandbox dir for the slug you get back.
- **A sandbox file bundles unrelated features.** That one coach file carried the admin menu AND a member-facing mission block AND a green CSS retheme of the member dashboard AND an AJAX endpoint. To remove only the menu, comment its `add_action( 'admin_menu', ... )` line and leave the file running; renaming it to `.disabled` would strip the member-side theme too.

## Hidden layers that change payout behaviour

- `wp-content/novamira-sandbox/smart-binary-guardrails.php` (class `SM_SB_Guardrails`) auto-loads on EVERY request and hooks order-completed + `sb_bonus_engine_processed`. It enforces a per-order payout cap (`sb_settings['max_payout_pct_per_order']`, default 50) and a 90-day activity gate — bonuses get written as `status='pending'` with a `[HELD]`/`[CAPPED]` note, logged to option `sm_sb_guardrails_cap_log` (+ an admin notice). A held/short bonus is often this guardrail, not a bug — read the note and the log option before debugging bonus math.
- `wp-content/mu-plugins/` carries much of this site's custom logic (custom-sejoli-bank, sb-affiliate-gate-settings, sm-sidebar-modern, sejoli-commission-autofix, fluentcrm-swsj-integration, …). Check the relevant mu-plugin before assuming the plugin is the only actor.
- Editing any sandbox `.php`: it auto-loads on every request, so a syntax error white-screens the site AND breaks the Novamira MCP JSON-RPC. Back it up, `php -l` the LOCAL copy before scp, `php -l` again on the server, then curl the site for 200; never add top-level echo/print.
- **Two payout engines share every Sejoli order — check for double-pay before trusting the pool cap.** Sejoli's OWN affiliate program is live on most products (`_sejoli_enable_affiliate=yes`; commission meta `_sejoli_commission|type` = `percentage`/`fixed` + `_sejoli_commission|number`, e.g. 21%), and `SB_Sejoli::on_order_complete` auto-approves those records (`status` 'pending'→'added' in `wplo_sejolisa_affiliates`) so they pay UNGATED — on top of the MLM stack (Komisi Langsung % + team). Sum Sejoli-affiliate% + MLM-direct% + team% before concluding the plan fits the 40-50% pool target; ~66% was reachable. When auditing or changing the plan, surface this and get the owner to pick ONE engine (Sejoli product affiliate flags vs `SB_Bonus_Direct`).

## Production data operations (wipe / reset / rebuild)

Rule 1 — take the full DB dump FIRST (see Site & access); it is the only undo.
Rule 2 — investigate READ-ONLY and CONFIRM before deleting. Real-looking names/emails are not proof of paying customers, but a mass delete on a wrong guess is unrecoverable. When the instruction is ambiguous (which rows) or the owner says "belum jalan" (pre-launch), get the confirmation in writing BEFORE the delete — even when told "kerjakan dulu".
Rule 2b — for a STRUCTURAL rebuild (re-shaping the HU tree, re-parenting thousands of members), pause and DRAW the intended structure for the owner before touching data. He asks for this explicitly ("tahan... coba gambarin") and what confirms it is a rendered diagram — an `::preview` HTML tree, not a text description or an ASCII sketch. "Tahan dulu" / "tunggu" mid-flight is an immediate stop: no further writes, no 'while I'm here' cleanup, until he re-scopes.
Rule 3 — run multi-step ops via a local `.php` file (`scp` to /tmp, then `wp eval-file /tmp/x.php --allow-root`); complex PHP through `wp eval '...'` over SSH mangles (bash+SSH quoting). Never touch `wplo_users` / `wplo_usermeta` — that is the Sejoli member base.
Rule 4 — verify after: re-query counts and spot-check the new structure.
Rule 5 — HU layout: default to a BALANCED 2-2 HU tree (7 HUs → `1 → left 2, right 5 · 2 → left 3, right 4 · 5 → left 6, right 7`), NOT an all-left tusuk-sate spine. A spine buries every member past the admin tree view's default depth and the owner reads it as an empty tree; confirm the shape before building.

Table list, the HU shape choice + reset-in-place and full-rebuild recipes, the `sb_members` uses `id` vs every other `sb_*` table uses `member_id` purge pitfall, the Sejoli→tree mapping, and the `wp eval` gotchas: `references/data-ops.md`.

## User's standing decisions (do not contradict)

- NO BV — points are the pairing unit, money is integer Rupiah. Never reintroduce BV math.
- WooCommerce & FluentCart integrations ON HOLD (unused by the business): don't fix, don't refactor, don't "improve". Sejoli is what pays.
- Simplify the plan toward 4 bonus types: Sponsor + Pairing + Matching + Milestone. Do not add bonus types without the user asking.
- **Anti-MLM wording is a hard requirement on every MEMBER-facing surface.** Before calling a member area clean, check the three places the wording hides — the rendered page is the least likely place: (1) `SB_Activator::create_member_pages()` page TITLES (an MLM-branded title and a "tree" title); (2) hard-coded registration hrefs inside `public/class-sb-shortcodes.php`; (3) `public/partials/member-tree.php`, a dead tree partial that still ships the old MLM vocabulary and a dev banner. Fixing the activator titles is NOT enough — those pages already exist in the DB, so rename them too (`wp_update_post([ 'ID'=>$id, 'post_title'=>..., 'post_name'=>... ])`), and resolve every link through `mlm_page_id('mlm_page_register')` + `get_permalink()` rather than a literal slug (WordPress keeps the old slug redirect, so the rename is safe). Member-facing vocabulary: 'Super Affiliate', 'Partner Binaan', 'Tim A/Tim B', 'Saldo Komisi', 'Pencairan Komisi'. The network tree stays ADMIN-ONLY — a member must never be able to pull their downline, including via AJAX.
- Admin UX (current state + rules): the menu is CONSOLIDATED — one 'Pengaturan Program' submenu whose SIX internal `?tab=` tabs (bonus / commission / packages / placement / triple-bundle / payout) are NOT WP submenu items; do not re-split it, and do not re-add the '— JARINGAN —' style section-header entries. When asked to reorganize the admin, change the CONFIG/content pages in the SAME pass as the menu — the user reads 'menu changed but config didn't' as 'nothing changed'. A 'design upgrade' must change LAYOUT, not just fonts/tokens/emoji→dashicons; token-only polish is rejected as 'gak berubah'. Any redesign must introduce ZERO errors (php -l / node --check everything).
- Production fix protocol: backup → fresh scp → patch → scp back → php -l → smoke test (site HTTP 200 + `wp eval 'echo "boot-ok";'`). Demo/seed endpoints must never touch production data (`SB_Seeder::clear()/run()` are gated behind a `SB_DEMO_MODE` constant — keep that gate).
- Cache-bust: admin CSS/JS are enqueued with `?ver=SB_VERSION`. ANY change to a `.js`/`.css` file requires bumping `SB_VERSION` (+ the Version header) in `smart-binary.php`, or browsers serve the stale asset; menu/PHP-only changes need no bump.

## Audit / fix workflow

Fan out parallel subagents by module with exclusive file ownership (see the `subagent-fanout` skill). scp the plugin to local scratch, flatten the nested dir, then dispatch. Write the exact FILE LIST into each brief and make sure no two children own the same file — a lost update is silent, because each child scp's its own copy back over the other's work.

Then, for late changes: `delegate_task(action='steer')` FAILS once the child has finished ('no live subagent in this conversation's spawn tree'). Check `action='list'` first; if the owner of those files is gone, make the edit yourself. Before patching ANY file after a parallel batch, RE-PULL it from the VPS — a child may have pushed a newer version, and patching a stale local copy silently reverts its fix (detect it by checking whether a fix you know the child made is present in the copy you just pulled).

Verify every audit claim against the code before reporting it to the owner. Auditors are usually right but do produce wrong line numbers and composed hook names your grep will not match (see 'Finding things on this site'); conversely, a claim you cannot reproduce by reading the code is not a finding. Bug inventory with file:line in `references/bug-inventory.md`.
