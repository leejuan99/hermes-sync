---
name: sejoli
description: "Use when working with Sejoli membership/affiliate plugin."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sejoli, wordpress, membership, affiliate, commission, smart-millionaire]
    related_skills: [novamira-mcp-troubleshooting]
---

# Sejoli (Membership & Affiliate plugin)

Sejoli powers membership + affiliate commissions on the Smart Millionaire WordPress site (`member.smartmillionaire.co.id`). Load this when the task touches Sejoli products, orders, member groups, commissions, or member access. A lot of what renders is overridden by site mu-plugins — list `wp-content/mu-plugins/` (bank fields, confirm OTO, sidebar/admin UI) before concluding "Sejoli core does X". For the tooling quirks of driving WordPress through Novamira (sandbox, heredoc quoting, editing plugin PHP via SSH), see `novamira-mcp-troubleshooting`.

## When to Use

- "How many orders/sales today?" or any order-count question.
- "What's the commission for [member group] on [product]?"
- "Find product X / give me the link."
- Member-access checks ("does user X have LUNAS access to product Y?").
- Building an addon/plugin on top of Sejoli (custom checkout, cart, catalog, multi-product orders) — internals map in "Checkout & order engine" below.

## Data model

- **Products** = CPT `sejoli-product`. Permalink `/product/<slug>/`. Get URL with `get_permalink($id)`, price with `get_post_meta($id,'_price',true)`, affiliate-on flag with `get_post_meta($id,'_sejoli_enable_affiliate',true)`.
- **Member tiers** = CPT `sejoli-user-group`. On this site: Free Member (3747), PLATINUM Member (433), SILVER Member (1812), GOLD Member (510).
- **Orders are NOT a post type.** They live in a custom Sejoli table — query via `sejolisa_get_orders()`, never `get_posts(['post_type'=>…order…])` (returns nothing; WooCommerce is inactive, `shop_order` is empty). Direct DB access is `{$wpdb->prefix}sejolisa_orders` — the prefix on this site is `wplo_`, NOT `wp_`, so a hardcoded `wp_sejolisa_orders` in `wp db query` fails with `table doesn't exist`; use `$wpdb->prefix` (or `wp eval` it) instead.

## Querying from Novamira execute-php

`$wpdb` is unavailable in the sandbox, and any `$var` or `=` must survive a **quoted** heredoc (`<<'EOF'`). Prefer direct function calls with literal args, then `echo json_encode(...)`:

```php
echo json_encode(get_posts(['post_type'=>'sejoli-product','s'=>'air','posts_per_page'=>20,'post_status'=>'publish']));
```

Use `get_post_meta($id,'key',true)` for scalars (price, commission) and `get_posts`/`get_page_by_path`/`get_the_title`/`get_post_field` for posts. Avoid `array_map`/closures — an unquoted heredoc strips `$f` to empty and you get `expects at least 1 argument`.

## Key functions (from Sejoli core)

- `sejolisa_get_user_access_products($user_id)` — products a member has LUNAS access to. Use this for access checks; do NOT use `sejolisa_does_user_have_access()`, which calls `display_block_access()` → `wp_die()` → blank page when access is missing.
- `sejolisa_get_orders(['user_id'=>..,'product_id'=>..])` — returns `['valid'=>bool,'orders'=>[...]]`; `status==='completed'` = LUNAS.
- `sejolisa_carbon_get_post_meta($post_id, 'field')` — reads Carbon Fields complex meta (the canonical reader for commission fields).
- Affiliate identity from an order: `sejolisa_get_order(['ID'=>$id])['orders']` carries `affiliate_id` + `affiliate_name` (display name, joined) + `product_id` + `status`. Affiliate phone is user meta — try keys `phone`, `user_phone`, `billing_phone`, `handphone`, `no_hp`, `whatsapp` in order; for wa.me links normalize by stripping non-digits and mapping `0…`→`62…`, `8…`→`628…`.

## Media, options & notifications (site ops)

- **Uploading images when CLI PHP lacks GD/Imagick:** `wp media import` fails with "No support for generating images found." (thumbnail generation needs GD). Working fallback: copy the file into `wp-content/uploads/YYYY/MM/` (then `chown www:www`), and `wp eval` a `wp_insert_attachment()` with `post_mime_type` / `post_title` / `post_status => 'inherit'` / `guid` = the public URL; set `update_post_meta($id, '_wp_attached_file', 'YYYY/MM/<file>')`, and if `wp_get_attachment_metadata()` is empty set a minimal `_wp_attachment_metadata` (`width`/`height`/`file`). Verify with `curl` HTTP 200 + `wp_get_attachment_url($id)`. (No sub-sizes are generated — fine for notification links and instruction pages.)
- **Product images = the WP featured image.** Sejoli has no product-image meta of its own — its checkout templates bind `get_the_post_thumbnail_url($id, 'full')`. Products without `_thumbnail_id` have no image anywhere; custom UIs must render styled placeholders (never fake an image), and the real fix is content work: set a Featured Image per product.
- **Buyer-facing payment/status texts are WP options, not template files:** e.g. `_on_hold_whatsapp_content` holds the buyer WhatsApp payment reminder (placeholders `{{buyer-name}}` / `{{order-detail}}`, and on this site the literal bank account line); per-product overrides live in `_sjp_notif_order_new_wa_body` / `_sjp_notif_payment_confirm_*`. To change what buyers actually receive, edit those options.
- **Editing Carbon Fields options by CLI: complex (repeatable) fields are NOT one serialized option.** `carbon_set_theme_option()` accepts the array but does not persist complex rows — the reader still returns the old value afterwards. Write the raw option keys instead, mirroring an existing row exactly: a row marker `_<field>|||<rowIndex>|value` = `_`, then one key per subfield `_<field>|<subfield>|<rowIndex>|0|value`. Verify TWICE: the wrapper reader (`sejolisa_carbon_get_theme_option()`) returns the new row AND the consumer that matters (e.g. `apply_filters('sejoli/payment/payment-options', [])` for manual channels) lists it — the reader check alone has passed while the consumer stayed empty.
- **No-notification test orders:** `sejolisa_create_order([...])` (functions/order.php) inserts a row and fires NO hooks — no emails/WA, no commissions. Args: product_id, order_parent_id, user_id, affiliate_id, coupon_id, quantity, status, payment_gateway (full `module:::subtype` strings resolve via `sejoli/payment/module`), type, grand_total, meta_data (PHP array; stored serialized). Ideal for E2E-testing buyer pages (`/checkout/thank-you?order_id=` is public, no login) and notification filters; for filter tests build the order array from the raw table row + `maybe_unserialize($row['meta_data'])` — that array shape is what the filter contract expects.

## Checkout & order engine (building addons)

Sejoli has **no multi-product order** — one order row = one product, table `{prefix}sejolisa_orders`. The native funnel's "checkout page" IS the product page (`/product/<slug>`); a bare `/checkout` route does NOT exist natively (a bare request 404s). Only `/checkout/loading`, `/checkout/thank-you`, `/checkout/renew` are registered (rewrite → query var `sejolisa_checkout_page`), so an addon can claim `/checkout` without touching native funnels.

Payment channels (manual transfer rows, QRIS): how the options list is built, creating a channel via raw Carbon keys, what renders on the thank-you page, and the notification append hook are in `references/payment-channels.md`.

Before writing any checkout/order addon, read `references/order-engine.md`: order creation flow + grand-total filter-chain priorities, the `sejoli/order/update-status` status funnel, payment-module resolution and gateway gating, the container-product pattern for multi-product transactions, commission-cache and notification-suppression quirks, checkout registration, coupon table structure, and how to copy the core source locally for grepping.

The multi-product checkout addon built on these internals ("Sejoli MultiCart", `C:\Users\pc\projects\sejoli-multicart`) is documented in `references/multicart-addon.md` — architecture, locked decisions, the storefront/drawer/checkout UI port, verified lint/package commands, remaining work. To re-skin a plugin UI from a design prototype, use the `wordpress-plugin-ui-port` skill.

## Commission model

Commissions are Carbon Fields "complex" (repeatable) fields, set at two levels and often empty at the product level (meaning: fall back to the group default). Full structure, example values, and the raw meta-key format: `references/commission-model.md`.

**Sejoli is not the only engine paying on these orders.** This site also runs a custom MLM engine ('smart-binary' — see the `smart-binary-mlm` skill) that hooks `sejoli/order/set-status/completed` and pays its OWN commissions on the same orders, and that integration auto-approves Sejoli's own affiliate records (`status` 'pending'→'added' in `{prefix}sejolisa_affiliates`). One sale can therefore pay BOTH Sejoli's native affiliate commission AND the MLM stack — sum both before answering "what does this sale pay".

## Confirm / thankyou page + custom HTML

- `/confirm/?order_id=<id>` is a Sejoli **template**, not a WP page — `get_page_by_path('confirm')` returns null. It's rendered by `SejoliSA\Front\Confirm::display_confirm_page()` → `template/checkout/confirm.php`, and is the bank-transfer payment-confirmation form.
- Per-product "Notifikasi" content (`product_notification_on_hold` / `payment_confirm` / `in_progress` / `completed` / `cancel` / `refund`, the "Notifikasi" tab) renders ONLY into email/WhatsApp templates via the `{{product-info}}` shortcode — it never appears on the web confirm/thankyou page. Its shortcodes include `{{affiliate-name}}`, `{{affiliate-phone}}`, `{{affiliate-email}}`, `{{commission}}`, `{{confirm-url}}`.
- Sejoli Panel's "Product Extras" meta box (`_sjp_post_confirm_redirect` + `_sjp_notif_*`) is redirect + email/WA only, and its template vars are buyer-only (`{nama}` `{email}` `{phone}` `{produk}` `{total}` `{status}`) — no affiliate vars, so it can't drive an affiliate WhatsApp button.
- There is **no stock field that renders custom HTML on the web `/confirm/` page**. The owner's post-purchase OTO (upsell) runs through mu-plugin `sm-confirm-oto.php` (`SM_Confirm_OTO`) and is **PER-PRODUCT**: meta box "🎯 OTO Halaman Konfirmasi (per produk)" on `sejoli-product`, meta `_sm_confirm_custom_html`, shortcodes `{{affiliate-name}}` `{{affiliate-phone}}` `{{affiliate-email}}` `{{buyer-name}}` `{{order-id}}` `{{product-name}}` `{{sitename}}` `{{siteurl}}` (`{{affiliate-phone}}` normalized to 62xxx for wa.me). A global-option experiment (`sm_confirm_oto_html`, one OTO for every order) was built and then reverted at the owner's instruction — do not reintroduce a global OTO setting.
- **Placement (owner-corrected, final): a LARGE full-width section below the confirm form, revealed only AFTER the buyer submits the confirmation form.** Not injected into the small `.sejoli-complete-confirm` box. Reveal by echoing a `display:none` wrapper + an inline script that un-hides it when `.sejoli-complete-confirm` becomes visible (poll `classList.contains('hide')` + `offsetParent`, plus a MutationObserver), with a fallback to show immediately if the box is absent.
- **Scripts do NOT execute when injected via `innerHTML`.** OTO HTML that carries `<script>` (countdown timer, Tailwind CDN) must be echoed DIRECTLY in the page inside a hidden wrapper — never `el.innerHTML = html` — because innerHTML-injected `<script>` is inert. Direct echo also starts any countdown on page load, before the section is revealed.
- The OTO's own `<style>body{...}</style>` leaks to the whole confirm page (it's a section inside the page, not a standalone page). `sm-confirm-oto.php` now auto-scopes it — `scope_css()` rewrites `body`/`html` selectors inside `<style>` blocks to `.sm-oto-scope` and wraps the OTO in that class. Do not ask the owner to strip `body{...}` by hand; if styles still leak, fix `scope_css()` instead.
- **"Tombol Setelah Bayar" (per-product button on the confirm page, e.g. "Buka Ruang Webinar"):** file `wp-content/novamira-sandbox/sejoli-check-order-completed-friendly.php`, meta box on the product edit screen, auto-detects the bridged webinar via `_swsj_paid_product_id` (falls back to a custom label+URL). It hooks `sejoli_ajax_check-order-for-confirmation` @1 and returns HTML in the JSON `message`; the confirm template's JS injects that message into `.sejoli-invoice-check p` — a `<p>`. Block elements or a `<style>` block in the payload make the browser close the `<p>`, so the markup lands outside the green box (owner's words: "rusak miring"). Fix pattern: keep the payload inline-only (`<span style="display:block">`), move the CSS to `wp_head` guarded by `sejolisa_verify_page('confirm')`, and hide the leftover confirm form with a small `wp_footer` script that watches for the message title.
- Orphaned meta keys like `_sslm_*` (`content_shortcode_on_thankyou`, `redirect_on_thankyou`, `access_on_thankyou`) mean a "thankyou-customization" plugin was removed — values survive in the DB but nothing renders them.

## Profile bank fields (structured, per-user)

The Sejoli default profile (`/member-area/profile/`, template `sejoli/template/profile.php`) ships ONE free-text field: `<textarea name="_bank_info">` ("Informasi Rekening"). On this site it was replaced by a structured UI via mu-plugin `sm-bank-fields.php` (+ `sm-bank-fields/profile-template.php`), which overrides the template through the `sejoli/template-file` filter (fires in `Endpoint::set_template_part`, `template_include` @999; second arg is the view slug, e.g. `profile`).

- Fields: bank **dropdown with logos** (BCA/Mandiri/BRI/BNI/BSI + "Lainnya"), nomor rekening, nama pemilik. Meta keys: `sm_bank_name`, `sm_bank_number`, `sm_bank_holder`.
- Logos live at `wp-content/uploads/sm-bank-logos/{bca,mandiri,bri,bni,bsi}.svg` (Wikimedia SVGs; must be served `image/svg+xml`).
- Save handler hooks `sejoli_ajax_update-profile` at priority 500 (core runs @999 and `wp_send_json` → dies, so hook earlier). It also syncs `mlm_bank_name|mlm_bank_account_no|mlm_bank_account_name`, `_bank_info`, `bank_info`, `sejoli_bank_info` (composed single line: `BANK NUMBER a.n. NAME`).
- **Lock policy**: mu-plugin `custom-sejoli-bank.php` blocks non-admin bank/phone meta edits once filled (`update_user_metadata` filter, `manage_options` bypass). The structured UI enforces a finer rule: **locked only when bank + number are both present** (payout-ready); users with incomplete data may self-complete, and the holder-name field stays editable for everyone. `SM_Bank_Fields::set_meta_unlocked()` temporarily removes the legacy filter for its own writes — the handler enforces the lock itself, so do NOT remove the legacy filter globally.
- **WP-CLI pitfall**: with no current user the legacy filter silently blocks writes; call `wp_set_current_user(<admin>)` before touching these keys. `update_user_meta` writes are also blocked mid-migration otherwise.
- **Test-script pitfall (caused a real incident):** never cast `wp_create_user()`'s return to int without checking `is_wp_error()` — `(int)$wp_error` == 1, so test saves silently land on **user 1 (the owner's account)**. Always `if ( is_wp_error( $uid ) ) { ... }`. Recovery path: `wp eval-file` restore from `_bank_info_sm_backup` (parsed back into `sm_bank_*`).
- **This DB has no unique index on `(user_id, meta_key)`** (only `umeta_id` PK) — duplicate meta rows exist; `get_user_meta` returns the first. Dedupe only after verifying both rows are byte-identical.
- Migration: `mu-plugins/sm-bank-fields/migrate.php` — run it as a dry-run first, then with `apply`. It parses the free text → structured, backs up the original to `_bank_info_sm_backup`, and rewrites `_bank_info` (legacy consumers: commission modal, admin, panel) only at high confidence. Parser rules, storage map, the lock-rule details, the audit queries and the parser regression test are in `references/bank-fields.md` — read that before touching the parser or re-running the migration.

## Member-area branding (sidebar/topbar logo)

The member-area sidebar+topbar come from `sejoli/template/header.php`: it renders the drawer header (`<div class="item header-menu">` with the logo + `sejoli_member_area_name` text) **only when `sejolisa_get_member_area_logo('full')` returns a URL** — that function reads the Carbon theme option `sejoli_setting_member_area_logo` (an attachment ID) and returns false if the attachment no longer exists. When it returns false the whole header block is skipped (drawer items start at y≈0 = "menu terlalu ke atas", no logo/name) and `sm-sidebar-modern.php`'s JS also skips injecting the user card + close button, because it looks for `.item.header-menu`.

Diagnosis recipe (fast): `wp eval 'var_dump( get_post( sejolisa_carbon_get_theme_option("sejoli_setting_member_area_logo") ) );'` → if null, the attachment was deleted; curl the referenced file URL → if 404, the uploads file is gone too. Same pattern for `sejoli_setting_logo` and `site_icon`.

Repair: (1) restore the physical file under `wp-content/uploads/<yyyy>/<mm>/` (the sibling site `smartmillionaire.co.id` often still has the same brand files — copy from there), then (2) recreate the attachment post with the ORIGINAL id via `wp_insert_post(['import_id' => $id, 'post_type' => 'attachment', ...])` + `_wp_attached_file` + `_wp_attachment_metadata` (empty `sizes` is fine; this box has no WebP GD support so crops can't be regenerated). Files under `wp-content/uploads/2025/01/` were wiped site-wide at some point — check every `/uploads/2025/01/` reference (grep code + `wp db query` on options) and restore the ones that are still referenced.

## Pitfalls

- Product-level `_sejoli_commission` is empty on most products — don't conclude "no commission" without also checking the buyer's group (`_group_commissions` global tiers + `_group_setup_per_product` overrides).
- Commission `type` is `fixed` (Nilai Tetap) or `percentage` (Persentase); a bare number without the type is ambiguous (e.g. `40` = 40%, not Rp 40).
- Member access has no admin bypass in Sejoli's raw access API — an administrator is still "no access" to a paid product unless they own it (relevant when the owner sees the locked form on their own campaign).
- `sejolisa_create_order()` inserts a row and NOTHING else — `sejoli/order/new` and `sejoli/order/set-status/*` only fire through `do_action('sejoli/order/create')` (Admin\Order::create) or when you fire them yourself. Rows written directly get no commissions, access, or notifications until you replay those hooks.
- `SejoliSA\Admin\Affiliate::set_commission` caches `current_commissions` per REQUEST — in a batch (multi-product checkout, bulk creation) products 2..N silently get product 1's commission tiers unless you re-call `setup_product_affiliate_data($product)` on the instance (grab it from `$wp_filter['sejoli/order/new']` by class) before each `sejoli/order/new`.
- Payment modules gate their `sejoli/order/new` listeners on exact gateway-string equality (`'manual' === $order_data['payment_gateway']`, moota/bca/bni/bri likewise). Internal/secondary orders in a batch must use a neutral gateway marker (e.g. `multicart`) or bank/moota modules write unique-code transaction rows for them. `apply_filters('sejoli/payment/module', $gw)` just `explode(':::', …)[0]` — any marker passes through.
- Coupon usage counting: `sejolisa_update_coupon_usage($code)` (by CODE) is the working function; `sejolisa_update_coupon_usage_by_id()` is an empty stub in core 1.15.5 — calling it silently counts nothing.
- `SejoliSA\Order::set_payment_gateway()` silently downgrades any gateway string missing from `apply_filters('sejoli/payment/available-payment-gateways', [])` to `'manual'` — a custom checkout that invents a gateway key must register it in that filter, or the order (and its instructions/notifications) behaves as plain manual transfer.
