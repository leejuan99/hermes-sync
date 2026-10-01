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

Sejoli powers membership + affiliate commissions on the Smart Millionaire WordPress site (`member.smartmillionaire.co.id`). Load this when the task touches Sejoli products, orders, member groups, commissions, or member access. For the tooling quirks of driving WordPress through Novamira (sandbox, heredoc quoting, editing plugin PHP via SSH), see `novamira-mcp-troubleshooting`.

## When to Use

- "How many orders/sales today?" or any order-count question.
- "What's the commission for [member group] on [product]?"
- "Find product X / give me the link."
- Member-access checks ("does user X have LUNAS access to product Y?").

## Data model

- **Products** = CPT `sejoli-product`. Permalink `/product/<slug>/`. Get URL with `get_permalink($id)`, price with `get_post_meta($id,'_price',true)`, affiliate-on flag with `get_post_meta($id,'_sejoli_enable_affiliate',true)`.
- **Member tiers** = CPT `sejoli-user-group`. On this site: Free Member (3747), PLATINUM Member (433), SILVER Member (1812), GOLD Member (510).
- **Orders are NOT a post type.** They live in a custom Sejoli table — query via `sejolisa_get_orders()`, never `get_posts(['post_type'=>…order…])` (returns nothing; WooCommerce is inactive, `shop_order` is empty).

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

## Commission model

Commissions are Carbon Fields "complex" (repeatable) fields, set at two levels and often empty at the product level (meaning: fall back to the group default). Full structure, example values, and the raw meta-key format: `references/commission-model.md`.

## Pitfalls

- Product-level `_sejoli_commission` is empty on most products — don't conclude "no commission" without also checking the buyer's group (`_group_commissions` global tiers + `_group_setup_per_product` overrides).
- Commission `type` is `fixed` (Nilai Tetap) or `percentage` (Persentase); a bare number without the type is ambiguous (e.g. `40` = 40%, not Rp 40).
- Member access has no admin bypass in Sejoli's raw access API — an administrator is still "no access" to a paid product unless they own it (relevant when the owner sees the locked form on their own campaign).
