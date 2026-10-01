# Sejoli Commission Model

Commissions are Carbon Fields **complex** (repeatable) fields stored in post meta. Canonical reader: `sejolisa_carbon_get_post_meta($post_id, 'field')`.

## Two levels

### 1. Product-level commission
Field: `_sejoli_commission` (complex, tabbed-vertical, header "Tier N").
Sub-fields per tier: `number` (amount) + `type` (`fixed` = Nilai Tetap, `percentage` = Persentase).
Set on the product edit screen under the "Komisi" separator. **Often empty** on most products.

### 2. Group-level commission (member tier)
On each `sejoli-user-group` post:
- `_group_commissions` — global commission tiers for affiliates in this group. Sub-fields `number`, `type`.
- `_group_setup_per_product` — per-product overrides (complex). Sub-fields: `product` (product id), `discount_enable`/`discount_price`/`discount_price_type`, and `commission` (nested complex with `number`+`type`).

### Verified example — PLATINUM Member (group ID 433)
- `_group_commissions` → number `40`, type `percentage` (40% commission globally).
- `_group_setup_per_product` → product `5859`, commission number `100`, type `percentage` (100% override for that one product).

So a platinum affiliate earns 40% on most products but 100% on product 5859. A different product with no group override inherits the global 40%.

## Raw meta-key format (Carbon Fields)
Complex field values live under keys shaped like:

```
_group_commissions|number|0|0|value
_group_commissions|type|0|0|value
_group_setup_per_product|product|0|0|value
_group_setup_per_product|commission:number|0:0|0|value
_group_setup_per_product|commission:type|0:0|0|value
```

Read a raw scalar directly (when `sejolisa_carbon_get_post_meta` is unavailable or you want one value):

```php
get_post_meta(433, '_group_commissions|number|0|0|value', true); // -> "40"
```

Enumerate all keys to discover shape: `array_keys(get_post_meta($group_id))`.

## Reading via execute-php (sandbox-safe)
No `$wpdb`, no assignment, quoted heredoc. Example:

```php
echo json_encode(array(
  'global_num'  => get_post_meta(433,'_group_commissions|number|0|0|value',true),
  'global_type' => get_post_meta(433,'_group_commissions|type|0|0|value',true),
  'pp_product'  => get_post_meta(433,'_group_setup_per_product|product|0|0|value',true),
));
```
