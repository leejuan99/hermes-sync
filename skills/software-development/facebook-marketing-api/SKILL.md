---
name: facebook-marketing-api
description: Work with Facebook Marketing API (Graph API), Conversions API (CAPI/MCP), and Ads API. Covers auth (System User tokens, Business tokens), campaign/adset/ad/creative management, insights, CAPI event sending, and token management.
license: MIT
metadata:
  author: Hermes Agent
  version: "1.0.0"
---

# Facebook Marketing API / MCP Skill

Use this skill for:
- **Graph API** — campaigns, ad sets, ads, creatives, insights, custom audiences
- **Conversions API (CAPI/MCP)** — server-side events (Purchase, Lead, AddToCart, etc.) via `https://mcp.facebook.com/ads` or `https://graph.facebook.com/v20.0/`
- **Auth** — System User tokens, Business tokens, long-lived token exchange, token refresh
- **Rate limits & errors** — 429 handling, 400 validation, 401 expiry, retry logic

## Quick Reference

| Task | Endpoint / Method |
|------|-------------------|
| Get ad accounts | `GET /v20.0/me/adaccounts` |
| Campaigns | `GET /v20.0/act_{AD_ACCOUNT_ID}/campaigns` |
| Ad Sets | `GET /v20.0/act_{AD_ACCOUNT_ID}/adsets` |
| Ads | `GET /v20.0/act_{AD_ACCOUNT_ID}/ads` |
| Creatives | `GET /v20.0/act_{AD_ACCOUNT_ID}/adcreatives` |
| Insights | `GET /v20.0/act_{AD_ACCOUNT_ID}/insights` |
| CAPI Events | `POST https://mcp.facebook.com/ads` or `POST /v20.0/{PIXEL_ID}/events` |
| Token Debug | `GET /v20.0/debug_token` |
| Long-lived token | `GET /v20.0/oauth/access_token` |

## Auth Setup (Required First)

### 1. System User Token (Recommended for Server/CAPI)
1. Meta Business Suite → Settings → System Users → Create System User
2. Assign **Admin** or **Advertiser** role on Ad Account
3. Generate token with permissions: `ads_read`, `ads_management`, `business_management`, `pages_show_list`
4. Token **never expires** (until revoked)

### 2. Long-Lived User Token (Alternative)
```bash
# Exchange short-lived (1hr) → long-lived (60 days)
curl "https://graph.facebook.com/v20.0/oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={SHORT_TOKEN}"
```

### 3. Verify Token
```bash
curl "https://graph.facebook.com/v20.0/debug_token?input_token={TOKEN}&access_token={APP_ID}|{APP_SECRET}"
```

## Core Patterns

### Base Config
```python
BASE_URL = "https://graph.facebook.com/v20.0"
MCP_URL = "https://mcp.facebook.com/ads"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
```

### Pagination Helper (All List Endpoints)
```python
def fetch_all(url, params=None):
    results = []
    while url:
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = None  # next URL already has params
    return results
```

### Rate Limit Retry (429)
```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))
```

---

## Graph API Examples

### Get My Ad Accounts
```python
r = session.get(f"{BASE_URL}/me/adaccounts", headers=HEADERS, params={"fields": "id,name,account_status,currency,timezone_name"})
accounts = r.json()["data"]
```

### List Campaigns (with filtering)
```python
params = {
    "fields": "id,name,objective,status,created_time,updated_time",
    "limit": 100,
    "filtering": '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED"]}]'
}
campaigns = fetch_all(f"{BASE_URL}/act_{AD_ACCOUNT_ID}/campaigns", params)
```

### Get Insights (Performance Data)
```python
params = {
    "fields": "campaign_name,impressions,clicks,spend,ctr,cpc,cpm,conversions,conversion_value,roas",
    "level": "campaign",  # or adset, ad
    "time_range": '{"since":"2024-01-01","until":"2024-01-31"}',
    "limit": 100
}
insights = fetch_all(f"{BASE_URL}/act_{AD_ACCOUNT_ID}/insights", params)
```

### Create Campaign
```python
payload = {
    "name": "Test Campaign",
    "objective": "OUTCOME_SALES",  # or OUTCOME_LEADS, OUTCOME_TRAFFIC, etc.
    "status": "PAUSED",
    "special_ad_categories": "[]"
}
r = session.post(f"{BASE_URL}/act_{AD_ACCOUNT_ID}/campaigns", headers=HEADERS, json=payload)
campaign_id = r.json()["id"]
```

---

## Conversions API (CAPI / MCP)

### Endpoint Options
| Method | URL | Use Case |
|--------|-----|----------|
| **MCP** | `POST https://mcp.facebook.com/ads` | Direct CAPI endpoint (needs `access_token` in body) |
| **Graph** | `POST /v20.0/{PIXEL_ID}/events` | Standard Graph API (token in header) |

### MCP Request Format
```python
capi_payload = {
    "data": [{
        "event_name": "Purchase",
        "event_time": int(time.time()),
        "event_id": "unique_event_id_123",  # dedup key (required)
        "action_source": "website",
        "user_data": {
            "em": ["hashed_email_sha256"],      # required for matching
            "ph": ["hashed_phone_sha256"],      # optional
            "fn": ["hashed_first_name_sha256"], # optional
            "ln": ["hashed_last_name_sha256"],  # optional
            "ct": ["hashed_city_sha256"],       # optional
            "st": ["hashed_state_sha256"],      # optional
            "zp": ["hashed_zip_sha256"],        # optional
            "country": ["hashed_country_sha256"],# optional
            "client_ip_address": "192.168.1.1", # optional but recommended
            "client_user_agent": "Mozilla/5.0...", # optional
            "fbc": "fb.1.1234567890.abcdef",    # fb click ID from _fbc cookie
            "fbp": "fb.1.1234567890.abcdef"     # fb browser ID from _fbp cookie
        },
        "custom_data": {
            "currency": "IDR",
            "value": 150000,
            "content_ids": ["PROD_123"],
            "contents": [{"id": "PROD_123", "quantity": 1, "item_price": 150000}],
            "content_type": "product"
        }
    }],
    "access_token": ACCESS_TOKEN,  # REQUIRED in body for MCP
    "test_event_code": "TEST_12345"  # optional: for test events in Events Manager
}

# MCP endpoint
r = requests.post("https://mcp.facebook.com/ads", json=capi_payload)
# OR Graph endpoint (token in header)
r = session.post(f"{BASE_URL}/{PIXEL_ID}/events", json={"data": capi_payload["data"]})
```

### Standard Events Reference
| Event | Required Custom Data |
|-------|---------------------|
| `Purchase` | `currency`, `value`, `content_ids`/`contents` |
| `Lead` | `currency`, `value` (optional) |
| `AddToCart` | `currency`, `value`, `content_ids` |
| `InitiateCheckout` | `currency`, `value`, `content_ids`, `num_items` |
| `AddPaymentInfo` | — |
| `CompleteRegistration` | — |
| `Contact` | — |
| `CustomizeProduct` | — |
| `Donate` | `currency`, `value` |
| `FindLocation` | — |
| `Schedule` | — |
| `StartTrial` | `currency`, `value`, `predicted_ltv` |
| `SubmitApplication` | — |
| `Subscribe` | `currency`, `value`, `predicted_ltv` |
| `ViewContent` | `currency`, `value`, `content_ids`, `content_type` |

### Hashing Helper (SHA256, lowercase, trimmed)
```python
import hashlib

def hash_val(v):
    return hashlib.sha256(v.strip().lower().encode()).hexdigest()

# Usage
user_data = {
    "em": [hash_val("user@example.com")],
    "ph": [hash_val("+628123456789")],
    "fn": [hash_val("John")],
    "ln": [hash_val("Doe")],
}
```

---

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Validation error | Check `error.error_user_msg` / `error.fbtrace_id` |
| 401 | Token expired/invalid | Refresh token or re-auth |
| 403 | Permission denied | Check token scopes / ad account role |
| 429 | Rate limited | Exponential backoff (respect `x-business-use-case-usage` header) |
| 500 | Server error | Retry with backoff |

```python
def handle_error(r):
    err = r.json().get("error", {})
    code = err.get("code")
    msg = err.get("message", "")
    fbtrace = err.get("fbtrace_id", "")
    if code == 429:
        wait = int(r.headers.get("Retry-After", 60))
        print(f"Rate limited. Waiting {wait}s... (trace: {fbtrace})")
        time.sleep(wait)
        return "retry"
    elif code in (401, 403):
        print(f"Auth error: {msg} (trace: {fbtrace})")
        return "auth_error"
    else:
        print(f"API Error {code}: {msg} (trace: {fbtrace})")
        return "error"
```

---

## Token Management

### Check Token Expiry
```python
r = session.get(f"{BASE_URL}/debug_token", params={"input_token": ACCESS_TOKEN, "access_token": f"{APP_ID}|{APP_SECRET}"})
data = r.json()["data"]
expires_at = data.get("expires_at")  # 0 = never expires (System User)
is_valid = data.get("is_valid")
scopes = data.get("scopes", [])
```

### Refresh Long-Lived Token (before 60-day expiry)
```python
# Must be done while token still valid
r = session.get(f"{BASE_URL}/oauth/access_token", params={
    "grant_type": "fb_exchange_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "fb_exchange_token": LONG_LIVED_TOKEN
})
new_token = r.json()["access_token"]
```

---

## Testing / Debugging

### Test CAPI Event (Events Manager → Test Events)
1. Get test event code from Events Manager
2. Include `test_event_code` in payload
3. Check Events Manager → Test Events tab

### Validate Pixel Setup
```bash
curl -X POST "https://graph.facebook.com/v20.0/{PIXEL_ID}/events" \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{"data":[{"event_name":"PageView","event_time":1234567890,"event_id":"test_1","action_source":"website","user_data":{"em":["hashed_email"]}}]}'
```

---

## Quick Start Script (Python)

Save as `fb_ads.py`:
```python
import os, requests, time, hashlib, json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Config
APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")  # System User token
AD_ACCOUNT_ID = os.getenv("FB_AD_ACCOUNT_ID")  # e.g., "1234567890"
PIXEL_ID = os.getenv("FB_PIXEL_ID")

BASE_URL = "https://graph.facebook.com/v20.0"
MCP_URL = "https://mcp.facebook.com/ads"

session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

def hash_val(v):
    return hashlib.sha256(v.strip().lower().encode()).hexdigest()

def fetch_all(url, params=None):
    results = []
    while url:
        r = session.get(url, headers=HEADERS, params=params)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 60)))
            continue
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = None
    return results

# Example: list campaigns
campaigns = fetch_all(f"{BASE_URL}/act_{AD_ACCOUNT_ID}/campaigns", {
    "fields": "id,name,objective,status",
    "limit": 50
})
print(f"Found {len(campaigns)} campaigns")
for c in campaigns[:5]:
    print(f"  {c['id']} | {c['name']} | {c['objective']} | {c['status']}")

# Example: send CAPI Purchase event
event = {
    "event_name": "Purchase",
    "event_time": int(time.time()),
    "event_id": f"evt_{int(time.time()*1000)}",
    "action_source": "website",
    "user_data": {
        "em": [hash_val("customer@email.com")],
        "client_ip_address": "1.2.3.4",
        "client_user_agent": "Mozilla/5.0..."
    },
    "custom_data": {
        "currency": "IDR",
        "value": 250000,
        "content_ids": ["SKU_001"],
        "contents": [{"id": "SKU_001", "quantity": 1, "item_price": 250000}],
        "content_type": "product"
    }
}
payload = {"data": [event], "access_token": ACCESS_TOKEN}
r = session.post(MCP_URL, json=payload)
print(f"CAPI response: {r.status_code} {r.json()}")
```

---

## Related Skills

- `make-api-shell-connection-workflow` — if routing FB data through Make
- `airtable` / `notion` / `google-workspace` — store fetched insights
- `vps-server-access` — run scheduled sync on VPS (aaPanel cron)