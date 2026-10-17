# Profile bank fields & free-text migration

Site: `member.smartmillionaire.co.id`. Subsystem that replaced Sejoli's free-text "Informasi Rekening" textarea with a structured bank → number → holder UI, plus the one-time migration of the existing free-text data (238 users on first run). UI stack and hooks live in SKILL.md ("Profile bank fields"); this file is the migration/parser/audit depth.

## Storage map (write all of them)

| Key | Written by | Notes |
|---|---|---|
| `sm_bank_name` / `sm_bank_number` / `sm_bank_holder` | `sm-bank-fields.php` | canonical structured data; `sm_bank_name` holds a dropdown key (`BCA`…`BSI`) or free text for "Lainnya" |
| `_bank_info` | Sejoli profile / this plugin | legacy free text; composed as `BANK NUMBER a.n. NAME` (single line) |
| `bank_info`, `sejoli_bank_info` | sejoli-panel / Carbon reads | kept in sync by `custom-sejoli-bank.php` |
| `mlm_bank_name`, `mlm_bank_account_no`, `mlm_bank_account_name` | smart-binary MLM dashboard + payout | sync so the MLM UI shows the same account |
| `_bank_info_sm_backup` | migration | original free text, written once, never overwritten |

## Lock policy (do not weaken without asking the owner)

`custom-sejoli-bank.php` filters `update_user_metadata`: for non-admins it returns `false` when a protected key (`_bank_info`, `bank_info`, `sejoli_bank_info`, `mlm_bank_*`, `_phone`, `phone`, `user_phone`) already holds a non-empty value and the new value differs (`manage_options` bypasses). The profile UI mirrors the lock (readonly fields + 🔒 note) and `SM_Bank_Fields::save_profile_bank()` early-returns for locked non-admins. Consequence to state plainly to the owner: a member whose bank data is incomplete (e.g. number but no bank name) cannot fix it themselves — the admin must, unless the lock is explicitly loosened.

## Migration mechanics

- `wp eval-file mu-plugins/sm-bank-fields/migrate.php` = dry-run report (counts + samples + low-confidence list); append `apply` to write.
- Parse from `_bank_info_sm_backup` when it exists, else `_bank_info`. Otherwise a re-run re-parses this plugin's own rewritten text and parser fixes can never land on already-processed users.
- **Set a current user first**: `wp_set_current_user(<admin id>)` at the top of the eval-file script. WP-CLI has no current user, so the lock filter sees the writes as a non-admin change and silently drops them (they still look successful from the script's side).
- Write order: `sm_bank_*` → composed `_bank_info` + `bank_info` + `sejoli_bank_info` → `mlm_*` (migration fills `mlm_*` only when empty; a user save always writes them).
- Idempotent: backup written once, re-runs converge on the same values.
- Quoting: write SQL/audit logic into a `.php` file and run it with `wp eval-file` — shell-quoting `wp db query` through `ssh "…"` breaks on nested quotes and parentheses.

## Parser rules (free text → bank / number / holder)

- Alias match with `\b` word boundaries; for short ambiguous aliases (`DANA`, `OVO`, `GOPAY`, `SHOPEEPAY`, `DKI`) require a digit on the same line — else a member named "Dana" reads as a bank.
- Number regex separator class must include space, dash **and dot**: `\d[\d\-\t .]{3,}\d|\d{6,}`. Indonesian accounts are routinely written `527.10.88.214` / `398.1411.488`; omitting dots silently drops the number and the row lands as "no number".
- Pick the candidate number **nearest the matched bank alias** (track offsets), not the longest: multi-bank texts (`Mandiri X … Bri Y`) otherwise pair bank A with number B.
- Deprioritize phone-like candidates (`08…`, or `62…` with ≥ 11 digits); fall back to them only when nothing else qualifies — e-wallet numbers (DANA/OVO) legitimately look like phones.
- Marker regex `a.n / a/n / atas nama / pemilik` needs token boundaries on BOTH sides (`(?<![A-Za-z])…(?![A-Za-z])`) — without them "Angelia Hartanti" truncates to "gelia Hartanti".
- Strip a leading `AN` / `A.N` / `NAMA` token from fallback candidates only when the token is complete, and skip lines containing branch markers (`KCP`, `KC`, `kantor`, `cabang`, `unit`) as holder candidates — a branch name is not a person.
- Confidence: high = bank + number + holder (legacy text is rewritten), medium = two of three (legacy text left alone), low = anything less. Report low-confidence rows to the owner instead of guessing.

## Verify before and after every run

1. Regression test: `wp eval-file mu-plugins/sm-bank-fields/test-parser.php` — 20 cases, all must PASS before applying. PHP is not installed on the Windows box: edit/patch the test locally, copy it to the VPS, run it there.
2. Weird-input sweep on the sources: dotted numbers, numbers < 8 digits, `08xx`/`62xx` (phone-like), holders containing digits or > 40 chars, duplicate account numbers across users.
3. Coverage counts before vs after: users with `_bank_info` non-empty, rows written per key, backups present.
4. Spot-check ~10 random users with `SM_Bank_Fields::get_user_bank($uid)` after applying, and one locked non-admin + one fresh user through the rendered template (`wp eval` + `include` the template with `set_query_var('member',1)` / `('view','profile')`).
