# Fake Contact Detection Patterns

Complete detection rules used in the contact analysis session (2,287 contacts analyzed, 828 flagged).

## Detection Rules

### 1. Typo Domains (High Confidence)

| Pattern | Example | Correct |
|---------|---------|---------|
| `@gmal\.com$` | `ijoelhan1@gmal.com` | `gmail.com` |
| `@gamil\.com$` | `sinta12@gamil.com` | `gmail.com` |
| `@gmial\.com$` | — | `gmail.com` |
| `@yahooo\.com$` | — | `yahoo.com` |
| `@hotmial\.com$` | — | `hotmail.com` |
| `@outlok\.com$` | — | `outlook.com` |
| `@dmain\.com$` | `sarikem@dmain.com` | `domain.com` or `gmail.com` |

**Action**: Auto-fix or delete. These are almost always user typos.

### 2. Gibberish/Random Local Parts (High Confidence)

| Pattern | Regex | Example |
|---------|-------|---------|
| Random consonants (6+) | `[bcdfghjklmnpqrstvwxyz]{6,}` | `tyyurvvbggf` |
| Long digit sequences (5+) | `[0-9]{5,}` | `8020604`, `2811`, `2361` |
| Keyboard walks | `qwerty\|asdfgh\|zxcvbn\|qazwsx` | — |
| Repeated characters | `(.)\1{4,}` | `aaaaaa`, `bbbbbb` |
| High entropy (>70% unique chars) | `len(set(local)) / len(local) > 0.7` | `iciciffiff` |

**Action**: Delete. These are bot-generated.

### 3. Gibberish First Names (High Confidence)

| Pattern | Regex | Example |
|---------|-------|---------|
| Random consonants (5+) | `[bcdfghjklmnpqrstvwxyz]{5,}` | `Dhbdbdbdbd`, `Cicicic` |
| Very short (1-3 chars) | `^[a-z]{1,3}$` | `Oki`, `Nur`, `Boy` |
| Unusually long (>25 chars) | `len(name) > 25` | — |
| Email as name | `name == email` | `donywahyudi84@gmail.com` |

**Action**: Delete. Real names don't look like this.

### 4. Name/Email Mismatch (Medium Confidence)

**Heuristic**: Significant name parts (3+ chars) don't appear in email local part, AND email local part doesn't contain name parts.

```python
def name_email_mismatch(name, email):
    name_clean = name.lower().replace(' ', '').replace('.', '').replace('-', '')
    local = email.split('@')[0].lower()
    if len(name_clean) < 4:
        return False
    # Check if any 3-char substring of name in email
    name_parts = {name_clean[i:j] for i in range(len(name_clean)) for j in range(i+3, min(i+6, len(name_clean)+1))}
    email_parts = {local[i:j] for i in range(len(local)) for j in range(i+3, min(i+6, len(local)+1))}
    return len(name_parts & email_parts) == 0
```

**Examples**:
- `spydey2008@gmail.com` → "Erwin" (no overlap)
- `travisoptimumindonesia@gmail.com` → "Ali" (no overlap)
- `pubg.djawir@gmail.com` → "iqbal yusuf" (no overlap)

**Action**: Review manually. Could be real user with different display name.

### 5. Disposable Email Domains (High Confidence)

Known disposable/temporary email domains:
```
10minutemail.com, guerrillamail.com, mailinator.com, tempmail.com,
throwaway.com, fakeinbox.com, trashmail.com, yopmail.com,
getnada.com, maildrop.cc, sharklasers.com, grr.la,
temp-mail.org, disposetable.com, maildrop.io
```

**Action**: Delete. These are throwaway addresses.

### 6. Suspicious Keywords in Local Part (Medium Confidence)

Keywords suggesting test/fake accounts:
```
test, fake, dummy, spam, trash, temp, example, sample,
demo, null, void, asdf, qwer, zxcv, qwerty, 123456
```

**Action**: Review manually. Could be legitimate (e.g., "test.user@company.com").

## Summary Statistics (from session)

| Category | Count | Confidence |
|----------|-------|------------|
| Typo domains | 138 | High |
| Gibberish local part | 23 | High |
| Gibberish first name | 46 | High |
| Name/email mismatch | 529 | Medium |
| Short/random name | 115 | Medium |
| Long number sequence | 23 | Medium |
| Disposable domain | 0 | High |
| Manual flag | 8 | High |

**Total flagged**: 828 / 2,287 (36%)

## Recommended Actions by Confidence

### Delete Immediately (High Confidence)
- Typo domains (138)
- Gibberish local parts (23)
- Gibberish names (46)
- Email-as-name (1)
- Disposable domains (0 found)
- Manual flag definite fakes (8)

### Review Manually (Medium Confidence)
- Name/email mismatch (529) — check if real users
- Short names (115) — could be nicknames
- Long numbers (23) — could be birth years, IDs

### Keep
- Clean contacts (1,472) — no flags

## Implementation Notes

The detection was implemented in Python during the session. Key files:
- `suspicious_contacts.json` — Full flagged list with reasons
- `all_suspicious_ids.json` — Unique IDs for bulk operations
- `manual_flagged_ids.json` — 8 definite fakes

To re-run detection on fresh data:
```python
# Load contacts, apply rules, output suspicious_contacts.json
```