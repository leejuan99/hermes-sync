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
- Wave 2 (not yet dispatched at audit time): admin menu reorg by category + UI/UX redesign (user wants ui-ux-pro-max / design-taste-frontend / redesign-existing-projects applied, zero errors).
