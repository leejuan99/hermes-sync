# Smart Binary — audit bug inventory

Source: parallel 6-agent audit of all ~77 PHP files (Oct 2026). ~58 findings.
Status legend: [FIXED] verified on VPS · [DISPATCHED] fix sent, unverified · [OPEN] not addressed · [HOLD] user parked it.

## Critical

1. `SB_Seeder::clear()` TRUNCATEs production tables — seeder.php:304; also REST /demo/clear rest.php:843. Gate behind SB_DEMO_MODE. [DISPATCHED]
2. `SB_Wallet::credit()` non-atomic read-modify-write — wallet.php:79 → atomic UPDATE balance=balance+x. [DISPATCHED]
3. `SB_Wallet::debit()`/`move_to_hold()` check-then-act race — wallet.php:105,163 → conditional atomic UPDATE WHERE balance>=x. [DISPATCHED]
4. `SB_Payout::approve()` sets 'paid' before/without hold release — payout.php:77 → claim row atomically, check release result. [DISPATCHED]
5. `create_triple_bundle()` inserts 3 members with same user_id (UNIQUE) — member.php:199 → drop unique, check insert results. [DISPATCHED]

## High

1. Woo/FluentCart never create SB_Subscription → pairing held forever — woocommerce.php:69. [HOLD — user: those integrations unused]
2. % sponsor/level bonuses computed on POINTS not money (~100000x underpay) — bonus-level.php:40, bonus-sponsor.php:34. [DISPATCHED]
3. Pairing consumes points BEFORE subscription gate → held bonus destroys volume — bonus-pairing.php:60. [DISPATCHED]
4. flush_all_carry flushes wrong month + carry row never re-read — bonus-pairing.php:122. [DISPATCHED]
5. Foundation-leg left_only ignored for directs #1-3 — member.php:305. [DISPATCHED]
6. activate() not idempotent (double BV/bonus on re-activation) — member.php:375. [DISPATCHED]
7. get_upline_chain() off-by-one (self at level 1) — tree.php:174. [DISPATCHED]
8. Period boundaries use server TZ not site TZ (7h shift) — period.php:28. [DISPATCHED]
9. Float money math + round(...,4) fractional IDR — wallet.php:55. [DISPATCHED]
10. Currency rate missing → silent 1:1 IDR conversion — currency.php:15. [DISPATCHED]
11. add_to_leg() select-then-insert race loses points — point-system.php:59 → ON DUPLICATE KEY. [DISPATCHED]
12. Payout reject() ignores return_from_hold() result — payout.php:108. [DISPATCHED]
13. Payout request() TOCTOU double-spend — payout.php:10. [DISPATCHED]
14. SB_FluentCart missing in autoloader map → fatal when active — autoloader.php:51. [DISPATCHED]

## Medium (picklist, ~20)

royalty/pool/teampool no idempotency guard [DISPATCHED]; engine propagates legacy sb_tree BV while pairing reads points (Woo/FluentCart never feed pairing) [HOLD w/ Woo]; record_bonus() approves without checking wallet credit (bonus-base.php:27); level-bonus compression not implemented (bonus-level.php:26); consume_pairs() ignores carry columns (point-system.php:128) [FIXED, verified on VPS]; release_held_bonuses() double-pays duplicate pairing [HELD] rows + re-pays legs after reactivation (subscription.php:86) [FIXED, verified on VPS]; product-commission unrounded float (product-commission.php:70); Sejoli cancel reverses points on wrong rows (sejoli.php:154); Woo refund reverses only personal_bv (woocommerce.php:92) [HOLD]; /demo/seed no env guard (rest.php:836); save_webinar unsanitized → stored XSS (rest.php:1238); SB_Gamification missing autoloader [DISPATCHED]; dbDelta PRIMARY KEY single-space (db.php:27); Telegram webhook unauthenticated (telegram.php:84); WA webhook signature optional (whatsapp.php:88); get_total_downlines() direct-only (member.php:469); placement 1-2-1 counts inactive directs (member.php:300); period close/open not idempotent (period.php:62); gamification reads non-existent setting keys (gamification.php:60).

## Low (picklist, ~19)

money columns INT instead of DECIMAL (db.php:371); missing index rank_id/status (db.php:29); SB_Affiliate dead map (autoloader.php:21); activator 'currency' vs 'default_currency' key mismatch (activator.php:86); propagate_bv builds column from possibly-NULL position (tree.php:41); get_subtree off-by-one (tree.php:70); has_rank_in_leg uses rank_id>=N not sort_order (tree.php:289); affiliate link null deref (member.php:415); foundation tracker race (tree.php:238); level-pairing ignores status (level-pairing.php:124); rankachievement dup assignment; faststart multiplier uses wrong base; currency format 0 decimals; Woo processed flag set too early [HOLD]; register_setting mlm_settings vs sb_settings mismatch (admin.php:165); Gemini key in URL query (ai.php:67); register redirect wrong option key (public.php:508); telegram mirror uses last template body (notification.php:46); REST nonce defense-in-depth only (rest.php:105); /settings returns plaintext secrets (rest.php:725).

## Verification notes

- Never trust a [DISPATCHED] item as fixed: wave-1 fix agents' results must be verified on the VPS (php -l + smoke test) before updating to [FIXED].
- Wave 2 (admin menu reorg + UI/UX redesign) and wave 3 (integrity fixes) have since shipped, so the entries above are HISTORICAL; treat the re-audit below as the current state of the code.

## Re-audit of the current code

Rule: a re-audit re-reads the file — several wave-1 items were still reachable through a second code path, and a claim you cannot reproduce by reading the code is not a finding. Composed hook names (`'wp_ajax_sb_' . $name`) make greps miss live hooks; verify against the loop arrays.

### CRITICAL (open)
- **`SB_Webinar` does not exist anywhere in the plugin** — no `class-sb-webinar.php`, no autoloader entry — yet `class-sb-rest.php` calls `SB_Webinar::live_state / count_registrants / register_url / room_url / get_all / save / delete / get_registrants`. Every `/webinars` REST route is a fatal 500 and the admin Webinars page cannot load. `SB_Core` guards its own use with `class_exists()`; the REST layer does not. Ship the class or guard/short-circuit the routes.
- **Sejoli order cancel reverses leg points on the WRONG row** — the add path credits only the buyer's ANCESTORS (the point-system walk starts at `parent_id`), but the cancel handler subtracts from the BUYER's own `sb_leg_points` row. Refunds corrupt the buyer's leg balances (clamped at 0) while the credited ancestor legs keep paying on refunded volume.
- **`points_to_monetary()` mis-classifies money as points** — `return ( $bv < $per ) ? $bv * $per : $bv;` with `$per = point_per_amount` (100000). Sejoli passes POINTS (result correct), WooCommerce passes MONEY, so any Woo order under Rp 100.000 is multiplied by 100.000 (~99.999× overpay). Duplicated in `bonus-level.php` and `bonus-sponsor.php`. [HOLD with Woo]
- **Direct 25% is wired into the SEJOLI path only** — `SB_Bonus_Direct::award()`'s sole caller is the Sejoli integration; `SB_Bonus_Engine::process_order()` (Woo/FluentCart) never calls it, so the headline bonus silently pays Rp 0 there. [HOLD with Woo]

### HIGH (open)
- `apply_caps()` reduces the PAID bonus, but `consume_pairs()` (bonus-pairing) still consumes the ORIGINAL pair count — points for unpaid pairs are destroyed. Consume only `floor($bonus / $pair_rate)` pairs.
- Package `daily_cap_pairs` is enforced per pairing RUN, and pairing only runs weekly/monthly — a member can be capped at N pairs for a whole month while the label and the income simulator sell it as N pairs/DAY.
- Held bonuses are released only from `SB_Subscription::activate()`, so bonuses held by the PV gate never reach the wallet when the member later qualifies.
- `add_child` writes the parent's tree pointer with an unconditional UPDATE and no transaction — two concurrent signups can claim the same empty slot, orphaning a member whose `parent_id`/`position` then disagree with `sb_tree`.
- `activate()` idempotency is a non-atomic SELECT-then-UPDATE — concurrent triggers double-award. Claim atomically first (`UPDATE ... WHERE status <> 'active'`, proceed only on rows_affected == 1).
- Rank upgrade compares rank PRIMARY KEYS and hardcodes `1` instead of `sort_order`; `consecutive_months` is written only on a rank CHANGE, so any rule needing consecutive months is unreachable.
- Modulo-by-zero: `% (int) sb_setting('pairing_left_bv',1)` — `sb_setting()` returns 0 for a stored 0, so saving 0 is a fatal `DivisionByZeroError` (gamification + the public dashboard). Clamp with `max(1, ...)`.
- `SB_Seeder::clear()` TRUNCATEs 9 tables but omits 7 member-keyed ones; TRUNCATE resets AUTO_INCREMENT, so re-seeding leaks stale points/pairs/claims onto recycled member ids.
- `propagate_bv()` builds the column name from `$member->position` — a null/empty position makes the SET clause malformed and the whole upline propagation fails silently.
- Pool / royalty / team-pool write their idempotency guard row BEFORE the credit loop, so a mid-way crash permanently blocks the re-run and members stay underpaid.
- `record_bonus()` marks a row `approved` (and notifies) even when the wallet credit fails.

### Security + member-visible leaks
- `ajax_search_sponsor()` was registered `nopriv` with NO nonce and NO capability → anonymous enumeration of member IDs + display names, plus email probing. Fixed by dropping the nopriv registration AND adding a nonce + login check inside the handler. [FIXED, verified on VPS]
- `ajax_get_member_tree()` let ANY logged-in member pull their full downline (names/IDs/BV/status) with only the generic public nonce. Now gated with `current_user_can('manage_options')` — the network tree is admin-only. [FIXED, verified on VPS]
- Activator auto-created member pages titled 'Daftar Member MLM' / 'Pohon Jaringan', and four shortcode buttons hard-coded `/daftar-member-mlm/`. Titles renamed in the activator, the live DB pages re-titled and re-slugged, and the links now resolve via `mlm_page_id('mlm_page_register')` + `get_permalink()`. [FIXED, verified on VPS]
- `is_mlm_page()`'s shortcode list is stale (four unregistered shortcodes in, six real ones out), so `public.css`/`public.js` are not enqueued on pages using the real shortcodes and `[sb_affiliate_dashboard]` never leaves its loading spinner. `enqueue_tree_assets()` reads `sb_page_tree` while the activator writes `mlm_page_tree` → dead branch, plus D3 loaded from a CDN for a shortcode that renders no tree. [FIXED in wave 3 — verify]

### Medium/low still open
`min_payout` (readers) vs the old `min_withdrawal` key; `get_by_user()` ambiguous for shared-user triple bundles; `SB_Wallet::get_hold_balance()` surfaces `sb_hold_ledger` (company withholding) as the member's "Hold" while the real pending-payout figure (`sb_wallet.hold_balance`) is displayed nowhere; double `$wpdb->prepare()` on the members search (a `%` in the search term breaks placeholder binding); unbounded `SELECT user_id FROM sb_members` in both user-search paths; `export_payouts` formats every row with the default currency instead of each payout's own; `save_webinar` passes params unsanitized; `sb_bonuses` has no UNIQUE `(bonus_type, reference_id)` backstop; autoship reminder fires for every active member every day with no dedup; FluentCart refund reads `mlm_bv` that `on_order_paid()` never writes; `shortcode_atts` tag name in `join_button`; `$_GET` array params echoed into hidden inputs (PHP 8 warnings); `member-prospects` usort comparator never returns 0; `public/partials/member-tree.php` is dead code (no includer) but still ships the old MLM vocabulary and a dev banner.
