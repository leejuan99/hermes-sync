# Sejoli MultiCart addon (multi-product checkout + storefront UI)

The user's own multi-product checkout addon for their Sejoli store — a non-destructive take on the core ideas of the commercial "Sejoli Commerce" addon (sejolicommerce.com). Built on the internals documented in `references/order-engine.md`.

## Where things live

- Dev copy: `C:\Users\pc\projects\sejoli-multicart\` (folder `sejoli-multicart`, classes prefixed `SMC_`, text domain `sejoli-multicart`). Git repo initialized there (initial commit `c91342c`).
- Target: VPS `194.127.192.52`, site `member.smartmillionaire.co.id` (WP + Sejoli 1.15.5, PHP 8.3). Edit plugin PHP via SSH — Novamira blocks `.php` writes outside its sandbox.
- Feature spec / parity reference: the docs at `sejolicommerce.com/docs` (24 pages: checkout, cart, bump offer, physical shipping, bundles, promo/coupon, embed, notifications, orders menu, fulfillment, settings, shortcodes, developer filters). Read those before extending features.

## Design decisions locked

- Non-destructive: own `/checkout` route (native bare `/checkout` does not exist); native product funnels untouched; all features OFF until enabled in Sejoli → MultiCart.
- Data: tables `{prefix}smc_cart_items` (cart lines; guest key `g<token>` via cookie `smc_cart_token` 30 days, member key `u<id>`, merged on `wp_login`), `{prefix}smc_groups` (transaction: user/affiliate/coupon, parent_order_id, status, subtotal/discount/grand_total), `{prefix}smc_group_items` (lines: unit_price, subtotal, discount, line_total, child_order_id).
- Container product auto-created on activation (option `smc_container_product_id`, marker meta `_smc_container`='yes'): `_price`=0, `_enable_sale`='no'.
- Order bridging (`SMC_Orders`): parent via `do_action('sejoli/order/create')` with the custom total on the `sejoli/order/grand-total` chain at priority 250; children via direct `sejolisa_create_order()` with `payment_gateway='multicart'` (neutral marker), `order_parent_id`=parent, line totals, then `sejoli/order/new` + initial `set-status` with notification callbacks muted; affiliate commission cache re-primed per product via `setup_product_affiliate_data` before each `order/new`; statuses mirrored on `sejoli/order/status-updated` (children stay notification-silent — the parent is the one that emails the buyer).
- Coupon usage bumps ONCE per transaction via `sejolisa_update_coupon_usage($code)` (the `_by_id` variant is a core stub — see `references/order-engine.md`).
- After submit the cart is cleared and the browser follows `redirect_link` to native `/checkout/loading?order_id=<parent>` so Tripay/manual payment flows run unchanged; empty-cart visits to `/checkout` redirect to the cart page.
- MVP scope: digital products only (physical and variant products rejected at add-to-cart with a message — phase 2 = multi-origin shipping + variants); single coupon (multi-coupon later); guest checkout registers the buyer via `sejoli/user/register`; existing email → ask to log in instead of creating a duplicate.
- Shortcodes: `[sejoli_multicart_cart]`, `[sejoli_multicart_catalog]` (search/sort/category/pagination via GET params), `[sejoli_multicart_button]`, `[sejoli_multicart_mini]`, `[sejoli_multicart_count]`. Settings page under the Sejoli menu (`crb_carbon_fields_container_sejoli.php` parent slug).
- Front assets: plain CSS/JS, no frameworks (their pages run Elementor); theme via `--smc-primary` CSS var. The `/checkout` route renders a standalone HTML shell (own `wp_head()`/`wp_footer()`); shortcodes render fragments inside theme pages (`SMC_Checkout::render($template, $vars, $standalone)`).

## File layout

`sejoli-multicart.php` (bootstrap) · `includes/class-smc-install.php` (dbDelta tables, container, default pages "Keranjang"/"Katalog") · `class-smc-cart.php` (cart engine) · `class-smc-coupon.php` · `class-smc-orders.php` (parent/child bridging, status mirror, notification suppression) · `class-smc-ajax.php` · `class-smc-checkout.php` (route + submit + coupon AJAX) · `class-smc-shortcodes.php` · `class-smc-settings.php` · `class-smc-plugin.php` (asset enqueue) · `templates/{cart,catalog,checkout,minicart}.php` · `assets/{css/smc.css, js/smc.js}`.

## Status & remaining work

v0.1.1: all independent-reviewer findings applied (child-gateway restore, atomic submit lock via the INSERT IGNORE option pattern, guest-cart clearing, coupon policy + rounding invariant, recurring-product block, cleanup cron); coupon math proven by a pure-logic harness at `…\cache\scratch\smc-tests\coupon-test.php` (runs under PHP 8.3 with WP stubs, no WordPress). v0.2.0: storefront/drawer/checkout UI port from the user's React prototype (section below). v0.2.2–v0.2.4: the user installed v0.2.0 on production themselves, then bug-fix waves shipped to that same live install (each redeploy announced; per-version ZIP + commit kept for rollback — deploy cadence in `wordpress-plugin-ui-port` step 8). Fix wave: `[hidden]`-override bugs (empty modal covering the catalog, discount row, collapse), server-side money via a `lines` map, site-wide drawer auto-inject, logo/mixed-content, responsive grid, and instant qty (optimistic + coalescing queue — recipe in the ui-port skill's `references/interaction-patterns.md`). Live on `member.smartmillionaire.co.id`, feature enabled.

Remaining:
1. QRIS payment method — DONE. Manual-transaction channel via raw Carbon keys, now named "QRIS" (key `manual:::QRIS-1`) with `logo` = the QRIS brand wordmark so the checkout option list shows the mark; the label filter keeps the image instead of stripping it. The QR poster URL lives in the plugin option `smc_qris_image_url`; on Sejoli's v2 thank-you page `SMC_QRIS` renders the branded layout (poster swap + download button + custom centered countdown, single centered column, mobile overflow fixed), and appends the QR poster link to WA/email order-detail notifications for on-hold QRIS orders only. Full recipe + all v2-thankyou quirks: the `sejoli` skill's `references/payment-channels.md`. Structural note: storefront pages render inside sejoli-panel's member layout (~630px content column), so the catalog grid shows ~2 columns on desktop — a full-width catalog treatment is still open work.
2. End-to-end test on live: add 2–3 products → `/checkout` → submit → Tripay → verify child orders, member access, commissions, and that the buyer gets exactly ONE notification (parent only).
3. Phase-2 features: physical/multi-origin shipping, variants, recurring, multi-coupon engine (pill UI already built for it), multi-item notification receipt, PPN per product.

## Caveats to carry forward

- Child orders carry `order_parent_id`=parent; native renewal lookups also read `order_parent_id` — fine for one-time products, revisit if subscriptions appear.
- Parent notifications still use the container product's notification content; a `sejoli/notification/shortcode` filter hook is planned to swap in a multi-product receipt.
- `smc_groups`/`smc_group_items` exist for reconciliation/reporting; the admin Orders list (Sejoli → Penjualan) still shows one row per child order plus the parent container row — a dedicated Multicart orders view is phase 3.

## UI design port (v0.2.0)

The storefront look was ported from the user's "sejoli-commerce" React prototype (`Downloads\sejoli-commerce-plugin-&-storefront-suite.zip`, extracted under `…\cache\scratch\sejoli-commerce-src`) into: storefront hero + catalog (cards, category pills with counts, search, sort, chip pagination), product detail modal (Deskripsi / Fitur & Akses / Jaminan tabs), right-side floating cart drawer (slide animation, stepper qty, AJAX refresh), and a 2-column "Checkout 1-Halaman Terpadu" (numbered step cards, coupon pill with remove-restores-totals, sticky collapsible summary, radio payment cards).

New pieces: `templates/mini-items.php` (drawer body partial, shared with the AJAX re-render), `SMC_Checkout::render_partial()`, and the drawer refresh endpoint `smc_cart_items` (returns rendered HTML + count + subtotal). AJAX contract otherwise unchanged: `smc_cart_add|update|remove|count|items` (nonce `smc_cart`), `smc_apply_coupon` (nonce `smc_coupon`), `smc_submit_checkout` (nonce `smc_checkout`, returns `redirect_link`).

Addon-specific rules:
- A re-skin touches ONLY `templates/*`, `assets/css/smc.css`, `assets/js/smc.js`. Endpoints, nonces, response fields and `includes/` logic stay frozen; bump `SMC_VERSION` + readme Stable tag instead, or browsers serve the old skin.
- Templates pass JS contract data as `data-*` attributes (`data-smc-add`, `data-smc-buy`, `data-pid`, `data-unit`, `data-value`); re-verify with the selector-contract gate (`wordpress-plugin-ui-port` skill) after every template change.
- Prototype features with no engine/data behind them stay OUT and are named in the handover: rating stars and strikethrough prices (Sejoli stores neither), bump offer / shipping / wallet / COD (phase 2).
- The auto-injected drawer must skip Sejoli's own checkout-flow pages too (`get_query_var('sejolisa_checkout_page')` — loading/thank-you), not just the plugin's `/checkout` route: a floating cart on a payment page reads as noise (and shows a meaningless 0 badge).
- Component CSS must out-specify the generic `.smc img` rule (`max-width:100%;height:auto`, specificity 0-1-1): a bare `.smc-payment__logo` (0-1-0) silently loses and brand logos render at natural size (the QRIS wordmark filled the whole payment tile). Write `.smc-payment .smc-payment__logo { height:28px; max-width:96px; object-fit:contain }` — two classes beat class+element. When a `height` rule "doesn't apply", measure `getComputedStyle` and hunt for a competing generic rule before changing anything else.
- Logos from different sources carry different baked-in padding: equal box heights ≠ equal perceived size (BCA.png includes whitespace; the QRIS wordmark is tight-cropped). Tune to the VISIBLE mark's weight and confirm with a vision pass — box measurements alone will read as "balanced" while the tile still looks off.

## Admin settings surface (Sejoli → MultiCart)

The plugin panel consolidates the buyer-notification knobs in ONE page (the owner complained about editing split across two wp-admin locations):

- **Template editors**: "Konten WhatsApp" / "Konten Email" textareas for the on-hold ("Menunggu Pembayaran") notification — they read/write the SAME options Sejoli itself uses (`_on_hold_whatsapp_content` / `_on_hold_email_content`), so both UIs stay in sync and the native notification pipeline is untouched. Save via `update_option` + `wp_kses_post`.
- **Toggles**: `receipt_enabled` (itemized receipt for multi-product orders) and `notif_payment_info` (per-gateway payment info on on-hold) — stored in the `smc_settings` option array; honored at the top of `maybe_receipt()` / inside `append_notification_line()`.
- **QRIS image URL** (`smc_qris_image_url`, plain WP option) with live preview; used by the thank-you page swap, the download button, and the WhatsApp/email link.
- CLI testing caveat: `check_admin_referer` fails in `wp eval-file` ("Tautan kadaluwarsa") even with `wp_set_current_user(1)` + fresh nonce — test `SMC_Settings::handle_post()` directly via `ReflectionMethod` instead; the nonce gate itself is fine (wp_verify_nonce self-test returns OK; the browser form works).

## Verified commands for this addon

```bash
# Lint every touched PHP file on a /tmp copy (never against the installed plugin):
tar czf - templates includes assets | ssh -i ~/.ssh/vps_key -p 2222 root@194.127.192.52 \
  "rm -rf /tmp/smc-lint2 && mkdir -p /tmp/smc-lint2 && tar xzf - -C /tmp/smc-lint2 && \
   cd /tmp/smc-lint2 && for f in \$(find . -name '*.php'); do /www/server/php/83/bin/php -l \$f; done"

# JS syntax + selector contract (comm output must be EMPTY):
node --check assets/js/smc.js
grep -o "data-smc-[a-z-]*" assets/js/smc.js | sort -u > /tmp/js_sel.txt
grep -roh "data-smc-[a-z-]*" templates includes | sort -u > /tmp/tpl_sel.txt
comm -23 /tmp/js_sel.txt /tmp/tpl_sel.txt

# Ship a fix to the live install (announce first; bump SMC_VERSION + rebuild ZIP in the
# same pass). Tar from the PROJECT'S PARENT dir so the tarball is not inside the tree
# being archived ('file changed as we read it'); piping the tar into `ssh 'bash -s'`
# with a heredoc silently kills the pipe — scp the tarball instead:
cd "C:/Users/pc/projects" && tar czf smc-deploy.tgz --exclude='sejoli-multicart/.git' sejoli-multicart && scp -i ~/.ssh/vps_key -P 2222 -q smc-deploy.tgz root@194.127.192.52:/tmp/ && rm -f smc-deploy.tgz
# then over ssh: cd .../wp-content/plugins && rm -rf sejoli-multicart && tar xzf /tmp/smc-deploy.tgz && chown -R www:www sejoli-multicart

# Installable ZIP from git (single top folder, no .git), then verify the listing:
git archive --format=zip --prefix=sejoli-multicart/ -o "C:/Users/pc/Desktop/sejoli-multicart-<ver>.zip" HEAD
```

Hand-over: Desktop ZIP + wp-admin GUI update steps (Plugins → Add New → Upload Plugin → "Replace current with uploaded" → Ctrl+F5). While the user iterates on live, fixes ship straight to the installed plugin over SSH — announce every redeploy and keep a per-version ZIP + commit so rollback is one file. Never push a build the user has not been told about.
