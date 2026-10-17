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

## Multi-coupon (best-of engine)

- `SMC_Coupon::best_of( $codes, $items )` — computes EVERY entered code (find → validate → calculate on the ORIGINAL items), then picks the best discount **PER PRODUCT LINE** (sejolicommerce docs semantics: NO stacking; each line takes its largest single-coupon discount; different products may use DIFFERENT coupons simultaneously; ties → first entered wins). Returns `lines[]` (pid → discount), `coupons[]` (contributors), `primary` (largest contribution — stored on the group row), and `results[]` per code `{code, valid, message, discount = contribution, applied = contribution > 0}`.
- `smc_groups` keeps only ONE coupon slot (coupon_id/coupon_code) — store the PRIMARY contributor; usage is bumped for EVERY contributing coupon in `handle_submit` AFTER the whole transaction succeeds (create_orders must NOT bump by itself — it was moved out).
- Checkout UI: comma/;/newline-separated input (Enter applies), removable chips, dark count badge in the section title, per-coupon notes ('✓ X dipakai' vs 'ada diskon lebih besar'). JS state `couponCodes` array; removing a chip re-posts the remainder; invalid codes are dropped from state with their messages shown. Base line totals are snapshotted from `data-value` at init so 'all removed' restores exact original numbers.
- Live test coupons worth knowing: `VRS100K` (cart-wide fixed 100k/item), `FULL` (100% on products [5129,4867]), `NETWORKER10X` (20k/item on [5129]), `PROMOJULI` (100k total on [2205,387]), `RENEWMPO` (cart-wide 2jt/item — huge, use for winner tests carefully). Submit accepts `coupon_codes` comma-separated with `coupon_code` fallback.

## Checkout Bump Offer (Special Offer)

- Config in Sejoli → MultiCart: `bump_enabled`, `bump_product_id` (any sejoli-product except the container; the bump product stays independently purchasable — nothing locks it), `bump_price` (0 = product price; a LOWER value adds strikethrough + "Anda hemat" pill), `bump_description`, `bump_button_text`.
- Rendering: `SMC_Checkout::get_bump_offer($items)` in `maybe_render()` → `$smc['bump']` → card between the coupon section and payment methods (dashed amber, star icon, product row, two-way button; section carries `is-in-cart` + `data-bump-product`).
- Toggle: AJAX `smc_bump_toggle` (nonce `smc_cart` — the JS `post()` nonce map routes it to `SMC_CHECKOUT.cart_nonce`), `mode=add|remove`; add is idempotent (`SMC_Cart::add_bump()` never bumps quantity, (re)applies the override), remove deletes the line; JS reloads the page after a successful toggle.
- Price override: DB v2 adds `smc_cart_items.price_override` (double, default 0); `SMC_Cart::detailed()` uses it when > 0. The override flows the whole way: cart summary → checkout subtotal → `smc_group_items.unit_price` → child order totals (verified live: order 4131, child 4133 unit_price 238800 vs base 398000). Only apply an override when the configured price is lower than the product base price.
- Migration recipe: `maybe_upgrade()` runs on load whenever `smc_db_version` ≠ `SMC_Install::DB_VERSION` → add the column to the dbDelta schema array and bump the const; nothing else needed.
- Settings render smoke-test caveat: `SMC_Settings::render_page()` outputs nothing without caps under wp-cli — call `wp_set_current_user(1)` in `wp eval` first.

## Storefront /toko (front page)

- Shortcode `[sejoli_multicart_storefront]` (attrs: `products` = latest N, `title` override) renders `templates/storefront.php`: emerald gradient hero (pill + hero_title/hero_subtitle from settings, editable in Sejoli → MultiCart "Storefront / Halaman Depan") + INSTANT search box + category tiles (standard `category` taxonomy, `smc_cat` links into the catalog) + latest-products grid.
- Page `/toko` is auto-created by `ensure_default_pages()` (option `storefront_page_id`); `maybe_upgrade()` now re-runs `ensure_default_pages()` whenever `SMC_Install::DB_VERSION` bumps (v3), so adding another default page is just array/const work.
- Instant search: debounce 220ms → AJAX `smc_search_suggest` (nonce `smc_cart` via the standard `post()` helper; registered in `SMC_Shortcodes::init`; handler `SMC_Shortcodes::handle_search_suggest`). Rows render thumbnail + title + price; clicking navigates to `catalog_url?smc_q=<product title>`; Enter/Cari does the same with the raw query. Dropdown state lives in `[data-smc-suggest]` with `data-catalog-url`.
- Shared partials: `templates/parts/product-card.php` and `templates/parts/product-modal.php` — included by BOTH catalog.php and storefront.php (keep the selector contract when touching them).
- `auto_minicart()` now also injects the floating drawer on storefront pages (has_shortcode check extended).
- CLI caveat applies to suggest too: nonce gates fail under `wp eval` (`-1` output) — verify AJAX handlers in the browser, not wp-cli.

## Member area: collapsed list + unified detail (v0.2.20)

- Member area = Sejoli core's endpoint router (NOT sejoli-panel). List = `sejoli/template/order.php` DataTables `#orders`; native detail = jsrender modal; both fed by `/sejoli-ajax/*`. Row fields used by the renderer: `full.ID, product_name, quantity, coupon_code, order_parent_id, updated_at, created_at, type, affiliate_name, grand_total, status`.
- List collapse (additive): `SMC_Member_Endpoint` hooks `sejoli_ajax_smc-order-table` (router `sejoli/public/public.php:553`) → wraps `sejolisa_get_orders($filter, $table)` (first arg = filter map; `$table` = start/length/order[]/filter[date-range]) with user_id forced; `SMC_Member::collapse_rows()` merges parent+children+container per `meta_data.smc.role/group_id` into ONE row (clones parent; adds `smc_group_id`, `smc_items`; over-fetch `length*2` capped 400 then slice — pagination counts are an upper bound). Response envelope = native `{draw, data, recordsTotal, recordsFiltered}`. Native rows pass through untouched.
- Wiring: `SMC_Member::enqueue()` on `wp_enqueue_scripts` prio 1000 (after Sejoli's 999; guarded `sejolisa_is_member_area_page('order')`) repoints `sejoli_member_area.order.table.get_order_table` via `wp_add_inline_script(..., 'before')` + config `'after'`; `assets/js/smc-member.js` reads `$('#orders').DataTable().rows()` and on `draw.dt` replaces `.order-detail-trigger` with a `DETAIL MULTICART (N produk)` link for rows with `smc_group_id`. Any JS failure = native list (graceful).
- Detail view: filter `sejoli/template-file` maps view `multicart` → `templates/member/order-detail.php`; URL via `sejoli_get_endpoint_url('multicart','order')` + `{group_id}/` → `/member-area/multicart/order/{id}/`. Template renders inside `sejoli_header()/sejoli_footer()`, ownership guard = `group.user_id` or `manage_sejoli_orders`. Securing content: summary from `wplo_smc_groups` + parent order (gateway/status), items from `wplo_smc_group_items` ⋈ child `sejolisa_get_order()`.
- Access boxes mirror `sejoli/json/access.php`: attachments = `sejolisa_carbon_get_post_meta($pid,'attachments')` + filter `sejoli/attachments/links`; contents = postmeta `LIKE '%_product_association%'` → `sejoli-access` posts with `drip_day` gate (days since child order `updated_at`); status gate `completed|in-progress|shipping`, else "access opens after payment" note. Shipping block renders per-child `meta_data.need_shipment/shipping_data` (courier/service/cost/receiver/phone/address/postal_code/resi_number) — live once multi-origin lands.
- Testing gotchas: wp-login on this site lands members on `/dashboard-member/` (redirect_to ignored) — navigate to `/member-area/order/` manually after login; the browser harness `js()` 5s timeout can die on heavy pages — `ensure_real_tab()` recovers, wrap reads in retries; set test passwords via `wp_set_password()` for the qa-buyer accounts; `check_ajax_referer`-style gates fail under `wp eval` (CLI) but work in the browser.
- Known caveat: the container product still shows as an empty access card on `/member-area/akses/` (native `Model\Order::get_products()` has no filter) — future JS filter; also `sejoli-panel`'s own dashboard lists children (reads wplo_sejolisa_orders directly).

## Multi-origin shipping / multi-gudang (v0.2.21–0.2.22)

- **Provider**: reuses the store's EXISTING shipping integration — RajaOngkir/Komerce (`https://rajaongkir.komerce.id/api/v1/calculate/domestic-cost`, header `key: <sejolisa_carbon_get_theme_option('rajaongkir_pro_user')>`, form-urlencoded `origin`/`destination`/`courier`/`weight`). KiriminAja was NOT used (documented as a future adapter).
- **Rate semantics**: the API returns cost PER KG for the given weight; Sejoli's own display multiplies by `max(1, ceil(grams/1000))` — mirror that so our prices match the native checkout. Multi-courier = colon list (`jne:sicepat:jnt`); couriers with no service for a lane simply return nothing. Skip JNE trucking volume brackets (service names containing `<`/`>` — `JTR<130` etc).
- **Destination search**: reuse the native helper `sejolisa_get_district_options($term)` (functions/options.php, min 4 chars, results `[{id,text,district}]`, 1-month transient). Empty result is CACHED for 1 hour by the native function — delete `_transient_sejolisa_raongkir_district_<md5>` when debugging.
- **Data model**: tables `smc_warehouses` (label, contact, address, `district_id` = Komerce origin id, district_label, postal_code, active) + `smc_packages` (group_id, parent_order_id, warehouse_id, origin_label, weight, item_value, courier_code/name, service, service_desc, etd, cost, resi_number, status); columns `smc_group_items.package_key/weight`, `smc_groups.shipping_total/ship_to`. DB_VERSION '4' → dbDelta adds everything.
- **Product config**: our own meta `_smc_warehouse_id` + `_smc_weight` (grams) via a meta box on `sejoli-product` (`SMC_Shipping_Admin`), falling back to native `_shipment_weight` and the warehouse whose `district_id` matches native `_shipment_origin`. Weight falls back to option `shipping_default_weight` (1000) so nothing hard-blocks. Physical products are only sellable when `shipping_enabled` AND a warehouse is assigned (validate_product → WP_Error `smc_no_warehouse`).
- **Checkout**: section "2.7 Pengiriman (per Gudang)" between bump and payment — receiver/phone/address/postal + destination search widget (AJAX `smc_search_destination`), one card per origin package with item chips, weight, live courier radios (AJAX `smc_quote_shipping`, cheapest preselected, per-card cost + summary breakdown lines), shipping row + `[data-smc-total]` adjusted by DELTA (never recomputed from scratch, so coupon/qty math stays intact).
- **Submit**: server RE-quotes (`SMC_Shipping::resolve_choices()` — never trust client prices; falls back to the cheapest option with a note), sets `SMC_Shipping::set_pending([packages, shipping_total, ship_to])` BEFORE `create_orders`; parent grand total = group total + shipping (filter at prio 250), parent gets native-compatible `need_shipment`/`shipping_data{courier,service,cost,receiver,phone,address,postal_code,district_id,district_name}` via the `sejoli/order/meta-data` filter (single package → real courier name; multiple → `MULTI-KURIR` + "N paket dari M gudang"), children get the same keys with `cost => 0` (package cost lives on the parent) plus `smc_package`/`smc_origin`/`smc_etd`, packages persisted to `smc_packages`, group row updated with `shipping_total` + `ship_to` JSON.
- **LANDMINE (cost a live fatal)**: `sejolisa_update_order_meta_data()` runs `array_replace_recursive($current, $value)` on EVERY value — passing a scalar/boolean (`need_shipment => true`) throws `TypeError: Argument #2 must be of type array, true given` on PHP 8 and kills the whole request (order row created, group left in draft). Use `SMC_Orders::merge_order_meta()` instead (arrays deep-merged, scalars assigned).
- **Resilience**: `SMC_Orders::create_orders()` wraps `do_action('sejoli/order/create')` in try/catch and captures the parent row via a prio-1 `sejoli/order/new` listener (`capture_parent_order`) so a third-party listener blowing up (notifications, gateways) can never lose the order id or kill checkout.
- **Quote cache**: only SUCCESSFUL quotes are cached (6h). Caching empty/failed responses poisons a lane for hours when the API hiccups (rate limit) — a real bug caught in testing.
- Debug tooling that paid off: a temporary mu-plugin registering `register_shutdown_function` + `error_get_last()` → `wp-content/smc-fatal.log` (WP's "critical error" page hides the exception; WP_DEBUG is off on this site). Remove it after use.
- Environment note: `/usr/local/bin/wp` runs through `#!/usr/bin/env php` whose PHP has NO curl extension (the web SAPI — litespeed lsphp83 — does). php-cli `wp eval` fatal 'Call to undefined function curl_init()' inside the OneSender WA plugin is therefore a CLI-only red herring.
- Test data left on the store: warehouses "Gudang Semarang" (origin 65005 BOJONGSALAMAN) + "Gudang Jakarta" (17620 MENTENG), product 6470 → Semarang 7000g, 4237 → Jakarta 500g; successful e2e order 4141 (2 packages, SiCepat HALU 52.500 + 16.000 = 68.500, total 1.104.385 incl. unique code); failed attempts 4134–4140 cancelled.

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
