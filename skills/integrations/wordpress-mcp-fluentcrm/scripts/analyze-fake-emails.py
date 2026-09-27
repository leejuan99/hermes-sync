#!/usr/bin/env python3
"""
Analyze Fluent CRM contacts for fake/spam emails.

Usage:
    python analyze-fake-emails.py --input contacts.json --output suspicious.json
    python analyze-fake-emails.py --input contacts.json --output suspicious.json --min-confidence HIGH
"""

import json
import re
import argparse
import sys
from typing import Dict, List, Tuple

# ============ CONFIGURATION ============

DISPOSABLE_DOMAINS = {
    '10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'tempmail.com',
    'throwawaymail.com', 'fakeinbox.com', 'trashmail.com', 'yopmail.com',
    'getnada.com', 'maildrop.cc', 'sharklasers.com', 'grr.la', 'temp-mail.org',
    'dispostable.com', 'tempmail.net', 'mailnesia.com', 'mintemail.com',
    'spamgourmet.com', 'spambox.us', 'spamhole.com', 'spaminator.de',
    'spamcowboy.com', 'spamcannon.net', 'spamgourmet.org', 'spamherelol.com',
}

TYPO_DOMAINS = {
    'gmal.com': 'gmail.com',
    'gamil.com': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gnail.com': 'gmail.com',
    'yahooo.com': 'yahoo.com',
    'yaho.com': 'yahoo.com',
    'hotmal.com': 'hotmail.com',
    'hotmial.com': 'hotmail.com',
    'houtlook.com': 'outlook.com',
    'outlok.com': 'outlook.com',
    'outlokk.com': 'outlook.com',
    'dmain.com': 'domain.com',
    'gmaill.com': 'gmail.com',
    'gmailll.com': 'gmail.com',
}

KEYBOARD_PATTERNS = [
    'qwerty', 'asdfgh', 'zxcvbn', '123456', 'abcdef', 
    'qazwsx', 'wsxcde', 'zaq123', 'qazxsw', 'asdfjkl',
]

GIBBERISH_NAME_PATTERNS = [
    r'[bcdfghjklmnpqrstvwxyz]{5,}',  # 5+ consonants
    r'^[a-z]{1,3}$',  # 1-3 random letters
]

FAKE_KEYWORDS = [
    'test', 'fake', 'dummy', 'spam', 'trash', 'temp', 
    'example', 'sample', 'demo', 'null', 'void', 'bot',
]

# ============ SCORING FUNCTIONS ============

def score_contact(contact: Dict) -> Tuple[str, List[str]]:
    """Score a contact for fakeness. Returns (confidence_level, reasons)."""
    score = 0
    reasons = []
    
    email = contact.get('email', '').lower()
    if '@' not in email:
        return 'HIGH', ['Invalid email format']
    
    local, domain = email.split('@', 1)
    first_name = (contact.get('first_name') or '').lower().strip()
    full_name = (contact.get('full_name') or '').lower().strip()
    status = contact.get('status', '')
    source = contact.get('source', '')
    last_activity = contact.get('last_activity', '')
    
    # === HIGH CONFIDENCE (+10-15) ===
    
    # Disposable domain
    if any(d in domain for d in DISPOSABLE_DOMAINS):
        score += 15
        reasons.append(f'Disposable email domain: {domain}')
    
    # Email used as name
    if first_name == local or full_name.replace(' ', '') == local:
        score += 15
        reasons.append('Email used as name')
    
    # Random consonant string (6+)
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', local):
        score += 10
        reasons.append('Random consonant string in email')
    
    # Keyboard patterns
    for kp in KEYBOARD_PATTERNS:
        if kp in local:
            score += 10
            reasons.append(f'Keyboard pattern: {kp}')
            break
    
    # Repeated characters (5+)
    if re.search(r'(.)\1{4,}', local):
        score += 10
        reasons.append('Repeated characters (aaaaa, bbbbb, etc)')
    
    # Gibberish first name
    if first_name:
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', first_name) and len(first_name) > 6:
            score += 10
            reasons.append('Gibberish first name (consonant string)')
        if re.match(r'^[a-z]{1,3}$', first_name):
            score += 5
            reasons.append('Very short first name (1-3 chars)')
    
    # Specific known fake patterns
    if email in ['tyyurvvbggf@gmail.com', 'iciciffiff@jcicif.com', 'buni133@gmail.com']:
        score += 15
        reasons.append('Known fake pattern from production data')
    
    # === MEDIUM CONFIDENCE (+3-5) ===
    
    # Typo domains
    for typo, correct in TYPO_DOMAINS.items():
        if typo in domain:
            score += 3
            reasons.append(f'Typo domain: {typo} -> {correct}')
            break
    
    # High entropy random string
    if len(local) > 15 and len(set(local)) / len(local) > 0.7:
        score += 3
        reasons.append('High entropy random string')
    
    # Long number sequences
    if re.search(r'[0-9]{5,}', local) and len(local) > 8:
        score += 3
        reasons.append('Long number sequence in email')
    
    # Name/email mismatch
    if first_name and len(first_name) >= 3:
        name_clean = first_name.replace(' ', '').replace('.', '').replace('-', '')
        name_in_email = any(
            name_clean[i:j] in local 
            for i in range(len(name_clean)) 
            for j in range(i+3, min(i+6, len(name_clean)+1))
        )
        prefix_match = name_clean[:3] in local if len(name_clean) >= 3 else False
        suffix_match = name_clean[-3:] in local if len(name_clean) >= 3 else False
        
        if not (name_in_email or prefix_match or suffix_match):
            score += 2
            reasons.append('Name/email mismatch')
    
    # Fake keywords in local part
    for kw in FAKE_KEYWORDS:
        if kw in local:
            score += 5
            reasons.append(f'Fake keyword: {kw}')
            break
    
    # === POSITIVE SIGNALS (reduce score) ===
    
    # Real engagement
    if last_activity and last_activity != 'null':
        score -= 2
    
    # Legitimate source
    if source in ['FluentForms', 'WooCommerce', 'Manual', 'API']:
        score -= 1
    
    # Subscribed status with activity
    if status == 'subscribed' and last_activity:
        score -= 1
    
    # Name matches email reasonably
    if first_name and (first_name[:3] in local or first_name[-3:] in local):
        score -= 2
    
    # Corporate/edu/gov domains
    legit_tlds = ['.co.id', '.ac.id', '.go.id', '.or.id', '.sch.id', '.web.id', '.my.id']
    if any(domain.endswith(tld) for tld in legit_tlds):
        score -= 3
    
    # Known major providers with normal local parts
    major_providers = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'yahoo.co.id']
    if domain in major_providers and not any(r.startswith(('Random', 'Keyboard', 'Repeated', 'High entropy', 'Fake keyword')) for r in reasons):
        score -= 1
    
    # Clamp score
    score = max(0, score)
    
    # Determine confidence
    if score >= 10:
        return 'HIGH', reasons
    elif score >= 5:
        return 'MEDIUM', reasons
    elif score >= 2:
        return 'LOW', reasons
    else:
        return 'CLEAN', []


# ============ MAIN ============

def main():
    parser = argparse.ArgumentParser(description='Analyze Fluent CRM contacts for fake emails')
    parser.add_argument('--input', required=True, help='Input JSON file with contacts array')
    parser.add_argument('--output', required=True, help='Output JSON file for suspicious contacts')
    parser.add_argument('--min-confidence', choices=['HIGH', 'MEDIUM', 'LOW', 'CLEAN'], 
                        default='LOW', help='Minimum confidence to include in output')
    parser.add_argument('--stats-only', action='store_true', help='Only print statistics')
    args = parser.parse_args()
    
    # Load contacts
    with open(args.input, 'r') as f:
        contacts = json.load(f)
    
    print(f"Loaded {len(contacts)} contacts")
    
    # Analyze
    results = {
        'HIGH': [],
        'MEDIUM': [],
        'LOW': [],
        'CLEAN': []
    }
    
    for contact in contacts:
        confidence, reasons = score_contact(contact)
        if reasons or confidence != 'CLEAN':
            contact['_analysis'] = {
                'confidence': confidence,
                'reasons': reasons
            }
            results[confidence].append(contact)
        else:
            results['CLEAN'].append(contact)
    
    # Print stats
    print(f"\n=== ANALYSIS RESULTS ===")
    for level in ['HIGH', 'MEDIUM', 'LOW', 'CLEAN']:
        print(f"  {level}: {len(results[level])} contacts")
    
    if args.stats_only:
        return
    
    # Filter by min confidence
    confidence_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'CLEAN': 0}
    min_level = confidence_order[args.min_confidence]
    
    suspicious = []
    for level in ['HIGH', 'MEDIUM', 'LOW', 'CLEAN']:
        if confidence_order[level] >= min_level:
            suspicious.extend(results[level])
    
    # Save
    with open(args.output, 'w') as f:
        json.dump(suspicious, f, indent=2)
    
    print(f"\nSaved {len(suspicious)} contacts to {args.output}")
    
    # Print HIGH confidence for immediate action
    if results['HIGH']:
        print(f"\n=== HIGH CONFIDENCE - DELETE THESE ===")
        for c in results['HIGH']:
            a = c['_analysis']
            print(f"  ID {c['id']:4d} | {c['email']:35s} | {c.get('first_name',''):20s} | {', '.join(a['reasons'])}")


if __name__ == '__main__':
    main()