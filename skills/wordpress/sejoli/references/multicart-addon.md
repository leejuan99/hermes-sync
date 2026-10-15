# Sejoli MultiCart addon (multi-product checkout — build in progress)

The user's own multi-product checkout addon for their Sejoli store — a non-destructive take on the core ideas of the commercial "Sejoli Commerce" addon (sejolicommerce.com). Built on the internals documented in `references/order-engine.md`.

## Where things live

- Dev copy: `C:\Users\pc\projects\sejoli-multicart\` (folder `sejoli-multicart`, classes prefixed `SMC_`, text domain `sejoli-multicart`).
- Target: VPS `194.127.192.52`, site `member.smartmillionaire.co.id` (WP + Sejoli 1.15.5, PHP 8.3). Edit plugin PHP via SSH — Novamira blocks `.php` writes outside its sandbox.
- Feature spec / parity reference: the docs at `sejolicommerce.com/docs` (24 pages: checkout, cart, bump offer, physical shipping, bundles, promo/coupon, embed, notifications, orders menu, fulfillment, settings, shortcodes, developer filters). Read those before extending features.

## Design decisions locked

- Non-destructive: own `/checkout` route (native bare `/checkout` does not exist); native product funnels untouched; all features OFF until enabled in Sejoli → MultiCart.
- Data: tables `{prefix}smc_cart_items` (cart lines; guest key `g<token>` via cookie `smc_cart_token` 30 days, member key `u<id>`, merged on `wp_login`), `{prefix}smc_groups` (transaction: user/affiliate/coupon, parent_order_id, status, subtotal/discount/grand_total), `{prefix}smc_group_items` (lines: unit_price, subtotal, discount, line_total, child_order_id).
- Container product auto-created on activation (option `smc_container_product_id`, marker meta `_smc_container`='yes'): `_price`=0, `_enable_sale`='no'.
- Order bridging (`SMC_Orders`): parent via `do_action('sejoli/order/create')` with the custom total on the `sejoli/order/grand-total` chain at priority 250; children via direct `sejolisa_create_order()` with `payment_gateway='multicart'` (neutral marker), `order_parent_id`=parent, line totals, then `sejoli/order/new` + initial `set-status` with notification callbacks muted; affiliate commission cache re-primed per product via `setup_product_affiliate_data` before each `order/new`; statuses mirrored on `sejoli/order/status-updated` (children stay notification-silent — the parent is the one that emails the buyer).
- After submit the cart is cleared and the browser follows `redirect_link` to native `/checkout/loading?order_id=<parent>` so Tripay/manual payment flows run unchanged.
- MVP scope: digital products only (physical and variant products rejected at add-to-cart with a message — phase 2 = multi-origin shipping + variants); single coupon (multi-coupon later); guest checkout registers the buyer via `sejoli/user/register`; existing email → ask to log in instead of creating a duplicate.
- Shortcodes: `[sejoli_multicart_cart]`, `[sejoli_multicart_catalog]` (search/sort/category/pagination via GET params), `[sejoli_multicart_button]`, `[sejoli_multicart_mini]`, `[sejoli_multicart_count]`. Settings page under the Sejoli menu (`crb_carbon_fields_container_sejoli.php` parent slug).
- Front assets: plain CSS/JS, no frameworks (their pages run Elementor); theme via `--smc-primary` CSS var.

## File layout

`sejoli-multicart.php` (bootstrap) · `includes/class-smc-install.php` (dbDelta tables, container, default pages "Keranjang"/"Katalog") · `class-smc-cart.php` (cart engine) · `class-smc-coupon.php` · `class-smc-orders.php` (parent/child bridging, status mirror, notification suppression) · `class-smc-ajax.php` · `class-smc-checkout.php` (route + submit + coupon AJAX) · `class-smc-shortcodes.php` · `class-smc-settings.php` · `class-smc-plugin.php` (asset enqueue) · `templates/{cart,catalog,checkout,minicart}.php` · `assets/{css/smc.css, js/smc.js}`.

## Status & remaining work

Written: bootstrap, install, cart, coupon, orders, ajax, checkout, shortcodes, settings, plugin, `templates/cart.php`.

Remaining:
1. `templates/catalog.php`, `templates/checkout.php`, `templates/minicart.php`.
2. `assets/css/smc.css` + `assets/js/smc.js` (cart AJAX via `SMC` localized object, qty steppers, minicart drawer, checkout submit + coupon apply following `redirect_link`).
3. `render()` needs a standalone-HTML shell option for the `/checkout` route (shortcodes render fragments inside theme pages; the route needs a full page).
4. `readme.txt`; lint every file with the VPS PHP 8.3 (`php -l`), deploy to `member.smartmillionaire.co.id`, enable in Sejoli → MultiCart, then test end-to-end: add 2–3 products → `/checkout` → submit → Tripay → verify child orders, member access, commissions, and that the buyer gets exactly ONE notification (parent only).

## Caveats to carry forward

- Child orders carry `order_parent_id`=parent; native renewal lookups also read `order_parent_id` — fine for one-time products, revisit if subscriptions appear.
- Parent notifications still use the container product's notification content; a `sejoli/notification/shortcode` filter hook is planned to swap in a multi-product receipt.
- `smc_groups`/`smc_group_items` exist for reconciliation/reporting; the admin Orders list (Sejoli → Penjualan) still shows one row per child order plus the parent container row — a dedicated Multicart orders view is phase 3.
