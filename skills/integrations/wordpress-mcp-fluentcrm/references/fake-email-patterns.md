# Fake Email Detection Patterns

Complete regex patterns and rules for identifying fake/spam emails in Fluent CRM contacts.

## High Confidence Patterns (Delete Immediately)

### 1. Random/Gibberish Local Parts
```regex
# 6+ consecutive consonants (no vowels)
[bcdfghjklmnpqrstvwxyz]{6,}

# Keyboard patterns
(qwerty|asdfgh|zxcvbn|123456|abcdef|qazwsx|wsxcde)

# Repeated characters (5+)
(.)\1{4,}

# Long random alphanumeric (high entropy)
^[a-z0-9]{15,}$  # with char diversity > 0.7
```

### 2. Known Disposable Email Domains
```
10minutemail.com
guerrillamail.com
mailinator.com
tempmail.*
throwaway.*
fakeinbox.com
trashmail.com
yopmail.com
getnada.com
maildrop.cc
sharklasers.com
grr.la
temp-mail.org
dispostable.com
```

### 3. Gibberish Names
```regex
# First name: 5+ consecutive consonants
[bcdfghjklmnpqrstvwxyz]{5,}

# First name: 1-3 random letters only
^[a-z]{1,3}$

# First name matches email local part exactly (email as name)
```

### 4. Specific Flagged Patterns (from production data)
```
tyyurvvbggf@gmail.com        # random consonants
iciciffiff@jcicif.com        # gibberish domain + name
buni133@gmail.com            # suspicious
donywahyudi84@gmail.com      # email as name
pepythe@gmail.com            # "Peppy the" - obvious fake
Cicicic                      # gibberish name
Dhbdbdbdbd                   # gibberish name
```

## Medium Confidence Patterns (Review Required)

### 1. Typo Domains (Fixable)
| Typo | Correct | Count (typical) |
|------|---------|-----------------|
| @gmal.com | @gmail.com | 23 |
| @gamil.com | @gmail.com | 92 |
| @gmial.com | @gmail.com | - |
| @dmain.com | @domain.com | 23 |
| @yahooo.com | @yahoo.com | - |
| @hotmal.com | @hotmail.com | - |
| @hotmial.com | @hotmail.com | - |
| @outlok.com | @outlook.com | - |

**Action:** Export list → verify if real users → bulk update or delete.

### 2. Name/Email Mismatch
```python
# Heuristic: significant name parts not in email local part
name_clean = first_name.lower().replace(' ', '').replace('.', '').replace('-', '')
local_part = email.split('@')[0]

# Check if any 3+ char substring of name appears in email
name_in_email = any(
    name_clean[i:j] in local_part 
    for i in range(len(name_clean)) 
    for j in range(i+3, min(i+6, len(name_clean)+1))
)

# Also check first 3 and last 3 chars
prefix_match = name_clean[:3] in local_part if len(name_clean) >= 3 else False
suffix_match = name_clean[-3:] in local_part if len(name_clean) >= 3 else False

mismatch = not (name_in_email or prefix_match or suffix_match)
```

**Examples:**
- `spydey2008@gmail.com` → "Erwin" (mismatch)
- `travisoptimumindonesia@gmail.com` → "Ali" (mismatch)
- `pubg.djawir@gmail.com` → "iqbal yusuf" (mismatch)

**Note:** Many Indonesian users register with "cool" emails but real names. Review unsubscribed first.

### 3. Short Names (1-3 chars)
```
Oki, Ana, Boy, Nur, Bin, etc.
```
Often real Indonesian nicknames. Check `last_activity` and `source` (FluentForms = likely real).

### 4. Long Number Sequences
```regex
[0-9]{5,}  # in local part, with total length > 8
```
Examples: `hy8020604@gmail.com`, `nurainiaja0045@gmail.com`, `kamis2811@gmail.com`

Often birth dates or phone fragments. Could be real.

### 5. Suspicious Custom Domains
```
pakekor@gocloud.my.id
```
Verify domain legitimacy (whois, website check).

## Low Confidence (Likely Real)

- Gmail/yahoo/outlook with normal-looking local parts
- Corporate domains (`@company.com`)
- Educational domains (`@university.ac.id`)
- Government domains (`@go.id`, `@kominfo.go.id`)
- Names matching email (e.g., `john.doe@gmail.com` → "John Doe")
- `source: "FluentForms"` with recent `last_activity`
- Tags/lists indicating legitimate funnel enrollment

## Scoring Algorithm

```python
def score_email(contact):
    score = 0
    reasons = []
    
    email = contact['email'].lower()
    local, domain = email.split('@')
    first_name = contact.get('first_name', '').lower()
    
    # High confidence (+10 each)
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', local):
        score += 10; reasons.append('Random consonant string')
    if re.search(r'(qwerty|asdfgh|zxcvbn|123456)', local):
        score += 10; reasons.append('Keyboard pattern')
    if re.search(r'(.)\1{4,}', local):
        score += 10; reasons.append('Repeated chars')
    if any(d in domain for d in DISPOSABLE_DOMAINS):
        score += 15; reasons.append('Disposable domain')
    if first_name == local or contact['full_name'].lower().replace(' ', '') == local:
        score += 15; reasons.append('Email as name')
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', first_name):
        score += 10; reasons.append('Gibberish name')
    if re.match(r'^[a-z]{1,3}$', first_name):
        score += 5; reasons.append('Very short name')
    
    # Medium confidence (+3-5 each)
    for typo, correct in TYPO_DOMAINS.items():
        if typo in domain:
            score += 3; reasons.append(f'Typo: {typo} -> {correct}')
    if len(local) > 15 and len(set(local)) / len(local) > 0.7:
        score += 3; reasons.append('High entropy')
    if re.search(r'[0-9]{5,}', local) and len(local) > 8:
        score += 3; reasons.append('Long numbers')
    if first_name and not name_matches_email(first_name, local):
        score += 2; reasons.append('Name/email mismatch')
    
    # Confidence levels
    if score >= 10: return 'HIGH', reasons
    if score >= 5: return 'MEDIUM', reasons
    if score >= 2: return 'LOW', reasons
    return 'CLEAN', []
```

## Thresholds for Action

| Score | Confidence | Action |
|-------|------------|--------|
| ≥ 10 | HIGH | Delete immediately (or quarantine) |
| 5-9 | MEDIUM | Review manually; prioritize unsubscribed |
| 2-4 | LOW | Monitor; check engagement metrics |
| 0-1 | CLEAN | Keep |

## Production Results (2,287 contacts)

| Category | Count | % |
|----------|-------|---|
| HIGH (delete) | ~15 | 0.7% |
| Typo domains (fix) | 138 | 6% |
| MEDIUM (review) | 529 | 23% |
| LOW (monitor) | 146 | 6% |
| CLEAN | 1,460 | 64% |

**Key insight:** Majority of "suspicious" flags are name/email mismatches common in Indonesian signups. Focus on HIGH confidence + typo domains for quick wins.