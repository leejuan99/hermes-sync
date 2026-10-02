# Smart Binary — data operations (destructive ops, tree rebuild)

## Undo is a full DB dump — take it first
DB `thegamec_wp632`, WP prefix `wplo_`. Full dump ≈193 MB.
```
cd /www/wwwroot/member.smartmillionaire.co.id && \
  wp db export /www/wwwroot/backups/member-db-<label>-$(date +%Y%m%d-%H%M).sql --allow-root
```
A plugin-dir tar backs up CODE only; for DATA ops only the SQL dump restores state.

## MLM tables to reset (TRUNCATE) — never touch wplo_users / wplo_usermeta
`sb_members, sb_tree, sb_member_ranks, sb_bonuses, sb_wallet, sb_wallet_transactions, sb_hold_ledger, sb_payouts, sb_affiliate_links, sb_pool_distributions, sb_notification_logs, sb_leg_points, sb_lifetime_points, sb_transactions, sb_reward_claims, sb_member_packages, sb_subscriptions, sb_foundation_legs`

## Running the op
Write a local `.php`, `scp` it to `/tmp/<name>.php`, then
`cd /www/wwwroot/member.smartmillionaire.co.id && wp eval-file /tmp/<name>.php --allow-root`.
`wp eval '...'` with multi-line or backslash-containing PHP over SSH fails (`syntax error, unexpected token "\"`) — always use a file.

## wp eval gotchas (verified)
- `wp eval` runs with no WP user, so capability-gated code (the `admin_menu` hook, admin menus) does not run: `$menu`/`$submenu` come back empty. Forcing it (`do_action('admin_menu')` + `require wp-admin/includes/menu.php`) FATALS (`array_keys(): null`). To verify admin menu registration, grep the plugin's `register_menus()`/`config_tabs()` source or check the rendered page — do not trust `wp eval` for menu state.
- `wp db query "SELECT ..." --allow-root` is fine for plain SQL.

## Rebuild recipe: N-HU spine + balanced member placement
Used when the owner resets the tree and wants his own HU chain plus every member re-placed under the bottom HU, split evenly left/right.

1. TRUNCATE the MLM tables above (keep `wplo_users`).
2. Owner HU spine (tusuk sate): row 1 = owner (user_id 1, no parent). Rows 2..N = the SAME user_id 1, each `sponsor_id`/`parent_id` = the previous HU, `position='left'`, `depth` = index-1, `status='active'`; insert one `sb_tree` row per member and set the previous node's `left_child_id` to the new id. (The old `UNIQUE KEY user_id` on `sb_members` was dropped, so one WP user can own several member rows.)
3. Place every member under the LAST HU as a COMPLETE binary tree (balanced): members come from
   `SELECT user_id FROM wplo_usermeta WHERE meta_key='wplo_capabilities' AND meta_value LIKE '%sejoli-member%' AND user_id <> 1`.
   BFS-fill — keep a queue of nodes with <2 children; attach each member to the front node's next free side (left first), create the `sb_members` row (`parent_id`=that node, `position`=side, `depth`=parent depth+1) and the `sb_tree` row, then push the new node onto the queue.
4. Verify: total count; `SELECT depth, COUNT(*) FROM sb_members GROUP BY depth` should roughly double each level (= balanced); the bottom HU's `left_child_id`/`right_child_id` are set.

## Sejoli → tree mapping
- Member list = `wp_users` with role `sejoli-member` (usermeta `wplo_capabilities`).
- Sponsor pointer = usermeta key `_affiliate_id` (≈2,900 users).
- `wplo_sejolisa_affiliates` is the COMMISSION-records table (order_id, affiliate_id, product_id, commission) — NOT the sponsor tree; do not read it as sponsor relationships.
