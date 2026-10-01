---
name: mlm-comp-plan
description: "Use when designing or auditing MLM/affiliate comp plans."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [mlm, compensation-plan, affiliate, smart-binary, smartmillionaire]
---

# MLM / Affiliate Compensation Plan Design

## Context: Smart Millionaire
- member.smartmillionaire.co.id, custom WP plugin 'smart-binary' (points-based binary), Sejoli = only live order source. WooCommerce/FluentCart ON HOLD (user: belum kepake).
- User target: commission pool max 40-50% of revenue. User wants NO BV, NO MLM appearance — branded 'Super Affiliate'.

## Golden rules (user-approved)
1. Pool cap 40-50%. Always sum: direct% + pairing% + matching% + reward reserve. Leave buffer for promos.
2. Digital products COGS ~0. Direct = % of PRODUCT PRICE (money, NEVER points — the 100000x underpay bug came from computing % on points).
3. Points: admin sets fixed points per product (Rp 97rb course = 1 poin). A sale puts 1 poin into the REFERRER's leg (side = seller's position in tree).
4. Simple 4-bonus stack (approved): Komisi Langsung 25% · Bonus Tim Rp 30.000/pair (1 poin Tim A + 1 poin Tim B) · Bonus Kepemimpinan 10% x 3 generasi of Bonus Tim · Reward Race (pairs per period, RESETS at period end, default quarterly).
5. No lifetime carry (unbounded liability). Flush/reset per period. All money integer Rupiah + idempotent (per-transaction keys).
6. Placement: referral #1-#2 locked to Tim A (foundation), #3+ free with auto-weak default. 1 orang = 1 posisi (triple-bundle exists, not advertised).

## Rebranding map (user: no MLM words in member area; tree hidden from members, kept in admin)
member→Afiliasi/Partner · sponsor→partner perekrut · kaki kiri/kanan→Tim A/Tim B · pairing→Bonus Tim · wallet→Saldo Komisi · payout→Pencairan Komisi · tree→Struktur Tim (admin only) · upline→partner tim. Ban words: MLM, binary, sponsor, kiri, kanan, bonus pasangan, pohon jaringan.

## BIMA plan lessons
Copy: round bonus numbers (easy to tell), locked placement (1-2-1), tangible rewards ladder, tusuk-sate self-stacking. Avoid: unlimited-depth pairing (27%+ of join), uncapped rank royalty per-HU, matching 10+ generations, RO bonus >50% margin. Legal (AP2LI) != financially sustainable.

## Plugin file map (production VPS)
- SSH: `ssh -i ~/.ssh/vps_key -p 2222 -o StrictHostKeyChecking=no root@194.127.192.52`
- Plugin: /www/wwwroot/member.smartmillionaire.co.id/wp-content/plugins/smart-binary
- Dispatch: includes/bonuses/class-sb-bonus-engine.php. Core stack: bonus-direct/sponsor/pairing/matching. 13 other bonus classes = default-off candidates (disable via engine, never delete).
- Points: includes/core/class-sb-point-system.php (sb_leg_points, period_key YYYY-MM). Rewards: sb_reward_defs has period_months column; reward race = pairs per period, reset at close.
- Settings UI: admin/class-sb-settings.php get_bonus_fields() writes 'sb_settings' option (NOT 'mlm_settings' — that's a dead key).
- Member area: public/class-sb-public.php + public/partials/* (tree hidden here; progress card instead). Admin tree: admin/partials/page-tree.php.

## Production fix protocol (MANDATORY)
backup tar to /www/wwwroot/backups/ → scp fresh files → edit locally → scp back → php -l every file → site HTTP 200 + `wp eval 'echo "boot-ok";'` → bump SB_VERSION in smart-binary.php (header + constant) for JS/CSS cache bust. Never edit files another agent owns in the same wave.
