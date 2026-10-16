# Sejoli payment channels — manual transfer rows, QRIS, rendering & notifications

Verified against Sejoli 1.15.5 on the Smart Millionaire site. Order creation / gateway resolution internals live in `order-engine.md`; this file covers the channel options list, what renders where, and the notification append hook.

## How the payment options list is built

- Producer: `sejolisa_get_payment_options()` → `apply_filters('sejoli/payment/payment-options', [])` (functions/options.php). Each payment module attaches `gateway-key => ['label' => string, 'image' => url]`.
- Manual-transfer keys: `manual:::<BANKKEY>-<rowIndex>`, built from the theme-option rows `manual_transaction_info`: `<BANKKEY>` = the bank code, or for `bank = other` → `strtoupper(sanitize_title(bank_name))`; `<rowIndex>` = the row position.
- The orders table stores only the module part (`set_payment_gateway()` whitelists against `sejoli/payment/available-payment-gateways`, unknown → `manual`); the subtype is saved in order meta `meta_data['manual']['bank-chosen']`, and account/logo details are re-read from the settings row at RENDER time (`Manual::set_payment_info`) — never from the order.
- Adding a channel in wp-admin: Sejoli theme options → "Transaksi Manual" → bank = "Bank Lainnya" (`other`), fill bank_name / logo (image URL) / owner / account. Owner + account are REQUIRED fields even when unused (e.g. put the NMID in account for a static QRIS).

## Creating a manual-transaction row via CLI (Carbon complex field)

`carbon_set_theme_option()` does NOT persist complex (repeatable) fields — after it "runs", the reader still returns the old rows. Write the raw option keys instead, mirroring an existing row exactly:

- row marker: `_manual_transaction_info|||<rowIndex>|value` = `_`
- per subfield: `_manual_transaction_info|<field>|<rowIndex>|0|value` (fields: bank, bank_name, logo, owner, account, info)

Then verify BOTH the reader (`sejolisa_carbon_get_theme_option('manual_transaction_info')` → the new row present) AND the consumer (`apply_filters('sejoli/payment/payment-options', [])` → the new `manual:::...` key present). One check alone has passed while the feature stayed broken.

## Where a manual channel renders

- Thank-you = native route `/checkout/thank-you?order_id=`; the live design is the v2 template (`sejoli/template/checkout/v2/thankyou.php`, selected per the order product's `checkout_design` meta).
- v2 prints `payment_info.logo` — a channel row with a logo URL makes the image render NATIVELY, no template work needed.
- v2 prints the logo TWICE (a 35% cell and a third cell). Hide the duplicate in CSS rather than fighting the template (`td:nth-child(3) img[src*="..."]{display:none!important}`).
- Theme CSS constrains `.transfer .ui.table td img` (~70px regardless of your width rule). To show a scannable QR: `!important` on an attribute selector (`img[src*="qris"]`) PLUS widening the first cell (`td:first-child{width:230px!important}`), and verify with `getComputedStyle(img).width` — never by eyeball.
- Detect these pages from `wp_footer` via `get_query_var('sejolisa_checkout_page')` (loading / thank-you) — use it to scope injected styles and to suppress floating-widget noise on payment pages.
- The manual module's global unique-code option (`_manual_transaction_unique_code`) adds a unique code to ticket totals — for static QRIS that is desirable (buyer types the exact amount); leave it on.

## Notification hooks (buyer email / WhatsApp)

- Append per-order content with `apply_filters('sejoli/notification/content/order-detail', $order_detail, $media, $recipient_type, $data)` — `$media` is `'whatsapp'` or `'email'`; `$data['order_data']` is the order ARRAY (`ID`, `status`, `payment_gateway`, `grand_total`, `meta_data` — including `meta_data['manual']['bank-chosen']`).
- WhatsApp bodies are plain text (no wpautop; URLs auto-link); email bodies pass through wpautop → emit an explicit `<a href>` there.
- GUARD BY STATUS: decorate only `on-hold` (unpaid) orders with payment instructions — the same filter fires for completed/cancelled notifications too.
- Template-level alternative: register a merge tag via `sejoli/notification/shortcode` and have the owner place it in the body option (`_on_hold_whatsapp_content` etc.). Only worth it when the owner wants editorial control of placement; a conditional append needs no template edit.

## Thank-you page (v2): countdown & mobile-layout quirks

- **FlipClock rebuilds the container after DOM ready.** On the v2 thankyou page Sejoli's checkout JS runs `FlipClock` on `.countdown-payment-run` at document-ready and EMPTIES/replaces that container — any countdown node you inject during footer parse gets wiped. Mount UI from `window.load` plus a retry watchdog (e.g. `setInterval` ~24×250ms, stop once mounted).
- **The flip wrapper is the SAME element, not a child.** The target element itself receives class `.flip-clock-wrapper`, so `.smc-cd-on .flip-clock-wrapper{display:none}` matches nothing useful — hiding it would hide your custom node too. Hide its CHILDREN instead: `.flip-clock-divider` and `ul.flip`.
- **Kill the wrapper's layout width.** FlipClock CSS leaves `width:460px; margin:2em auto` on the element; with children hidden it still forces ~460px layout → horizontal scroll on 390px phones (scrollWidth 543 vs 390) even though nothing looks wide. Override to `width:auto!important;max-width:100%!important;margin:0!important;transform:none!important`.
- **The "Jatuh tempo" line is a SIBLING** of `.countdown-payment-run` inside `.countdown-payment`, not a child — style `.countdown-payment > p` too (font-style can be italic there).
- **Sejoli's decorative dot rows overflow mobile.** `.top-dots` / `.bottom-dots` spans (~10 dots, ~280px fixed row) inside `.thankyou` push `documentElement.scrollWidth` to ~543 at 390px viewport. Contain: `.thankyou .top-dots,.thankyou .bottom-dots,.thankyou .bottom-lines,.thankyou .section.dots{display:block!important;max-width:100%!important;overflow:hidden!important}` (note: also `.bottom-lines` exists as a third variant — grep the live DOM, don't guess names).
- **Finding mobile overflow when no box looks wide:** binary-search the DOM — walk body descendants, temporarily set `display:none` on each child, and keep descending into the child whose removal drops `documentElement.scrollWidth`. Dots/shadows don't show up in width-based scans because the individual elements are small.
- **QRIS thank-you layout (centered single column):** hide `tr:first-child td:nth-child(2)` (account-name text) and `td:nth-child(3)` (duplicate logo); total row = `tr:last-child` with `.price` sized up (~46px desktop / 38px mobile) and `text-align:center` (tds made `display:block;width:100%`); the "Penting!" note is `.transfer-info` (its `.segitiga` decoration can be hidden). The `Salin` button is sejoli-JS-bound — keep the native DOM and restyle via CSS only, don't rebuild the markup.
- **Browser-harness gotcha when verifying:** `Emulation.setDeviceMetricsOverride` persists across `browser_exec` calls — clear it explicitly (`Emulation.clearDeviceMetricsOverride`) before desktop checks, or the "desktop" pass silently renders at the previous mobile width.
