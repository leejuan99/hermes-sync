# Sejoli order & checkout engine (core v1.15.x)

How orders are actually created, moved and paid — the map for building any checkout/order addon on top of Sejoli. Verified against core 1.15.5 on the Smart Millionaire install.

## Route & URL map

- The native "checkout page" IS the product page: `/product/<slug>` renders the buy form directly. There is no native bare `/checkout` page (bare request 404s).
- Rewrites registered by `SejoliSA\Public\Endpoint` (query var `sejolisa_checkout_page`): `^checkout/loading$`, `^checkout/thank-you$`, `^checkout/renew$`, `^renew/{id}$`; plus `^confirm$` → `sejolisa_page=confirm` and `^member-area/...`.
- Front AJAX endpoints: `/sejoli-ajax/<action>/` (get-calculate, apply-coupon, submit-checkout, submit-login…). The JS posts there and follows `response.redirect_link`.
- Success flow: submit → `redirect_link = /checkout/loading?order_id=N` → loading page AJAX → `/checkout/thank-you?order_id=N` → the thank-you page fires `do_action('sejoli/thank-you/render', $order)` — that is where gateway plugins act (Tripay redirects to its payment page; manual shows bank instructions). Zero-total orders go straight to thank-you.
- Consequence for addons: register your OWN route (e.g. `^checkout/?$` + your own query var) — non-destructive, native funnels keep working. Never touch `/checkout/loading|thank-you|renew`.

## Order creation

Table `{prefix}sejolisa_orders`: ID, created_at, updated_at, deleted_at, order_parent_id, product_id, user_id, affiliate_id, coupon_id, payment_gateway, grand_total, quantity, type, status, meta_data (serialized).

- `sejolisa_create_order($args)` inserts ONE row, no hooks. Args: product_id, order_parent_id, user_id, affiliate_id, coupon_id, quantity, status ('on-hold' default), payment_gateway, type ('regular'), grand_total, meta_data. It resolves the gateway via `apply_filters('sejoli/payment/module', $gw)` before storing.
- The real pipeline is `do_action('sejoli/order/create', $order_data)` → `SejoliSA\Admin\Order::create` (hooked at 999). It resolves status (COD → in-progress; zero total → completed/in-progress by shipping), computes grand_total via the filter chain below UNLESS `grand_total` is passed explicitly (passing it skips the whole chain), then fires `sejoli/order/new` and `sejoli/order/set-status/{status}` and writes a status_log meta entry.
- `sejolisa_get_respond('order')` right after the action returns `['valid'=>…, 'order'=>row, …]` with the new ID.

### Grand-total filter chain — `sejoli/order/grand-total` ($total, $order_data)

| Priority | Listener | Effect |
|---|---|---|
| 100 | `Order::calculate_total` | product price (via `sejoli/product/price`, includes group discounts) × qty |
| 101 | variant | variant surcharge |
| 150 | subscription | signup fee etc. |
| 200 | `Admin\Coupon::set_discount` | coupon (only when coupon state was set earlier by `sejoli/checkout/is-coupon-valid`) |
| **250** | **← hook a custom/computed total here** | overrides calc+coupon, still lets PPN/shipment (300) and payment module (900) adjust |
| 300 | PPN `add_ppn_cost`, shipment `add_shipping_cost`/`add_markup_price` | |
| 900 | `Admin\Payment::set_price` → module `set_price` | manual unique-code add/sub, etc. |

`sejoli/recalculate/grand-total` runs after the chain (duitku only). To give a wrapper/container order a fully computed cart total: hook at 250 and return your number — payment-module adjustments (unique code) and PPN then still apply.

## Status changes

Single choke point: `do_action('sejoli/order/update-status', ['ID'=>…, 'status'=>…])` — used by the admin UI, `/confirm` submissions, and every gateway callback. It runs `Admin\Order::update_status`:

1. skips when old status == new status;
2. `sejoli/order/allow-update-status` filter can veto;
3. updates the row, then fires `sejoli/order/status-updated` ($order) and `sejoli/order/set-status/{status}` ($order);
4. `set-status/{status}` listeners do the real work: affiliate commission transitions (completed→added, cancelled/refunded→cancelled, on-hold/in-progress/shipped→pending), license, acquisition stats, notifications, member-group upgrade on completed (priority 199). smart-binary MLM also hooks `set-status/completed`.

Status written via `sejolisa_update_order_status()` directly skips ALL of step 3-4 — always move orders through `sejoli/order/update-status`.

### Mirroring one status to a batch of orders

Hook `sejoli/order/status-updated`, detect the "parent" order (marker inside serialized meta_data), then per child call `do_action('sejoli/order/update-status', ['ID'=>child, 'status'=>same])`. Guard against recursion (ignore events whose order is a child) and skip children already at the target status.

## Multi-product transactions (container-product pattern)

How Sejoli Commerce maps multi-product onto Sejoli's one-product-per-order world, reproducible:

- Container product: a `sejoli-product` with `_price`=0, `_enable_sale`='no' (closed → native checkout refuses to sell it), affiliate off, marker meta, hidden from catalogs/lists.
- Parent order = container product; `grand_total` = whole cart (grand-total hook at 250); carries the real payment gateway and coupon.
- Child orders = one per cart line: real product, `order_parent_id` = parent ID, line total after discount share, same status as parent, neutral gateway marker.
- Children get their own `sejoli/order/new` + initial `set-status/{status}` at creation (commissions, acquisition) and then follow the parent via the mirror hook. Member access, group upgrades, and per-product records work with zero extra code.
- Payment gateways only ever see the parent — children never go to `/checkout/loading` or `thank-you/render`.

## Payment modules & gateway strings

- Gateway option keys look like `manual:::BCA-0`, `tripay:::BRIVA` (from `apply_filters('sejoli/payment/payment-options', [])`). `get_payment_module()` = `explode(':::', $gw)[0]` — arbitrary markers pass through unchanged, so addons can use a private gateway marker for orders that must not trigger any payment module.
- Modules hook `sejoli/order/new` to write their transaction rows, gated on exact gateway equality (`'manual' == $order_data['payment_gateway']`, moota/bca/bni/bri likewise).
- Manual unique code: `Admin\Manual::set_price` reads latest manual-transaction row ID +1 (mod max) and adds/subtracts it in the grand-total chain (900); `save_unique_code` persists per order on `order/new`. It is INSTANCE state — orders created later in the same request can inherit the code unless gated out by the gateway marker.
- Tripay: creates its transaction and redirects on `sejoli/thank-you/render`; its callback fires `sejoli/order/update-status` with completed (digital) / in-progress (physical) / cancelled (expired).

## Notifications

- Listener: `SejoliSA\Admin\Notification` on `sejoli/order/set-status/{status}` (100/300) plus `sejoli/notification/order/{status}` (manual resend).
- To mute notifications for one order (e.g. child orders must not email the buyer), remove the callbacks whose object class contains `Notification` from `$wp_filter['sejoli/order/set-status/'.$status]` around the `update-status` call, then restore them (keep priority + callback key from `->callbacks`) inside `try/finally` so an exception can never leave buyer notifications permanently muted.
- Placeholder injection point for multi-product receipts: the `sejoli/notification/shortcode` filter.

## Checkout-time registration & user resolution

- Register: `do_action('sejoli/user/register', ['user_name'=>…, 'user_email'=>…, 'user_phone'=>…])` — `Admin\User::register` auto-generates an 8-char password when none given, creates role `sejoli-member`, stores `_phone` user meta, records affiliate cookie if present, fires the registration notification. Fetch afterward with `get_user_by('email', $email)`.
- Affiliate cookie: `sejolisa_get_affiliate_cookie()` → `['product'=>[pid=>affiliate_id], 'general'=>aid]`. Native precedence: permanent affiliate → coupon → link; the product's `sejoli_enable_affiliate` flag gates everything; exclude self-referral; verify with `sejolisa_user_can_affiliate_the_product($pid, $aid)`.
- `do_action('sejoli/checkout/check-cookie', $post_data)` binds the cookie per product but only sets instance state — for a multi-product cart, resolve the cookie per line yourself.

## Coupons

- Table `{prefix}sejolisa_coupons`: code, user_id, coupon_parent_id, `rule` (serialized: apply_only[] product IDs, cant_apply[], max_discount, use_by_affiliate, limit_affiliate_coupon, renewal_coupon), `discount` (serialized: value, type `percentage|fixed`, usage `per_item|total`, free_shipping), usage, limit_use, limit_date, status ('active').
- Lookup: `sejolisa_get_coupon_by_code($code)` returns the unserialized coupon array. Bump usage ONCE per transaction with `sejolisa_update_coupon_usage($code)` (takes the coupon CODE — `sejolisa_update_coupon_usage_by_id()` is an empty stub in core v1.15.5, a silent no-op) — native bumps via `sejoli/coupon/update-usage` inside `Admin\Order::create` when `order_data['coupon']` is set.
- Discount math (native): percentage → price × value/100; fixed+per_item → qty × value; fixed+total → value once; cap at `rule.max_discount`. Scope via apply_only/cant_apply.

## Product meta keys that matter

`_price`, `_enable_sale` ('yes' = open; ANY other value → closed per `sejolisa_is_product_closed()` — closed products refuse native sale but orders can still be written against them), `_product_type` (digital|physical), `_product_format`, `_payment_type`, `_sejoli_enable_affiliate` ('' = off), `_product_weight`, `_disable_sale_time`. Read carbon fields with `sejolisa_carbon_get_post_meta($id,'field')` (resolves `_field`).

`sejolisa_is_product_closed()` reads `$product->_enable_sale` and nothing in core ever assigns that property — it is WordPress ≥6.4 "meta as property" magic (`$post->_<meta_key>` resolves post meta lazily: `property_exists()` returns false yet plain reads and `isset()` work, and `get_object_vars()` won't list it). Don't hunt for a setter; a fresh `get_post()` already resolves it.

Variant detection: the carbon field is `product_variants` (complex; each row carries a nested `variant` list). To answer "does this product have variants", read `sejolisa_carbon_get_post_meta($id, 'product_variants')` and check non-empty — the sub-field name `variant` alone matches nothing.

## Working with the core source

- Copy the plugin dir locally for grepping via a tar pipe (scp -r stalls on ~8k small files): `ssh -i <key> -p 2222 root@<vps> 'tar czf - -C /www/wwwroot/<site>/wp-content/plugins sejoli' > sejoli.tar.gz && tar xzf sejoli.tar.gz`.
- Orientation greps: `includes/class-sejoli.php` is the full hook registry; `models/order.php` (order schema + create); `admin/order.php` (create / update_status); `public/checkout.php` (front flow + AJAX + rewrites); `admin/checkout.php` (do_checkout/do_calculation); `functions/order.php` (sejolisa_* API); `payments/*.php` (gateways).

## Admin menu placement

Sejoli's admin menu parent slug is `crb_carbon_fields_container_sejoli.php` (Carbon Fields theme-options container). Add addon pages with `add_submenu_page('crb_carbon_fields_container_sejoli.php', …)` on `admin_menu` at priority ≥1000 so Sejoli's own menus register first.
