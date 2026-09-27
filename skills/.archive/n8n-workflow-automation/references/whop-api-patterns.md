# Whop API Integration Patterns for n8n Workflows

## Overview
Whop provides a REST API for programmatic product management. This reference covers the key endpoints and patterns for building "RSS/Feed → Whop Product" automation workflows in n8n.

## Base URLs
- **Production**: `https://api.whop.com/api/v1`
- **Sandbox**: `https://sandbox-api.whop.com/api/v1`

## Authentication
- **Account API Key** (server-side, acts as your business): `Authorization: Bearer <WHOP_API_KEY>`
- **App API Key** (for Whop Apps): Different scope
- **OAuth** (for user-context actions)

> **Important**: Store API key in n8n credentials (Generic Credential → HTTP Header Auth: `Authorization: Bearer <key>`)

---

## Core Endpoints for Product Creation

### 1. Create Product
```
POST /products
```
**Required Body:**
```json
{
  "title": "Product Name (max 80 chars)",
  "company_id": "biz_xxxxxxxxxxxxx",
  "visibility": "visible|hidden|archived|quick_link",
  "headline": "Short marketing headline",
  "description": "Full product description",
  "route": "url-slug",
  "metadata": {},
  "external_identifier": "unique-source-id"
}
```

**Key Fields for Feed Automation:**
| Feed Field | → Whop Field | Notes |
|------------|--------------|-------|
| `<title>` | `title` | Truncate to 80 chars |
| `<description>` | `description` + `headline` | Split: first sentence → headline, rest → description |
| `<link>` | `metadata.source_url` + `external_identifier` | Use URL hash as external_identifier for dedupe |
| `<pubDate>` | `metadata.published_at` | ISO 8601 |
| `<enclosure>` (file) | Upload via Files API → attach to Experience | See below |

**Response:** Product object with `id: "prod_xxxxxxxxxxxxx"`

---

### 2. Create Plan (Pricing)
```
POST /plans
```
**Required Body:**
```json
{
  "product_id": "prod_xxxxxxxxxxxxx",
  "name": "Access Plan",
  "price_amount": 2999,        // in cents
  "price_currency": "USD",
  "billing_cycle": "one_time|monthly|yearly",
  "is_archived": false
}
```

**For WSO-style one-time purchases:** Use `billing_cycle: "one_time"`

---

### 3. Create Experience (Content Delivery)
```
POST /experiences
```
**Required Body:**
```json
{
  "app_id": "app_xxxxxxxxxxxxxx",    // e.g., "Courses", "Chat", "Files", "Custom App"
  "company_id": "biz_xxxxxxxxxxxxxx",
  "name": "Course Name",
  "is_public": false,
  "logo": { "file_id": "file_xxx" }  // optional
}
```

**Common App IDs (pre-installed on Whop):**
| App | Use Case | App ID Pattern |
|-----|----------|----------------|
| Courses | Video lessons, modules | `app_courses` |
| Chat | Community chat/discord-like | `app_chat` |
| Files | Direct file downloads | `app_files` |
| Forums | Discussion boards | `app_forums` |

> **Note**: App IDs are per-company. Use `GET /apps` to list available apps for your company.

---

### 4. Attach Experience to Product
```
POST /experiences/{experience_id}/attach
```
**Body:**
```json
{
  "product_id": "prod_xxxxxxxxxxxxx"
}
```

---

### 5. Upload Files (for digital downloads)
```
POST /files
```
**Multipart form:**
- `file`: binary
- `purpose`: `experience_asset` | `product_gallery` | `general`

**Response:** `{ "id": "file_xxxxxxxxxxxxx", "url": "https://media.whop.com/..." }`

Use returned `file_id` in Experience `logo` or Course lesson attachments.

---

## Complete Automation Flow (n8n)

```
Cron (schedule)
    ↓
HTTP Request: GET RSS Feed (with auth headers if needed)
    ↓
XML Node: Parse RSS → JSON (fieldToSplit: "rss.channel.item")
    ↓
SplitInBatches (batchSize: 1)
    ↓
Function: Map RSS → Whop payload + dedupe check
    ↓
IF: Already processed? (check external_identifier in static data / file / DB)
    ├── Yes → Continue (skip)
    └── No  → Continue
    ↓
HTTP Request: POST /products (create product)
    ↓
HTTP Request: POST /plans (create pricing)
    ↓
HTTP Request: POST /experiences (create content container)
    ↓
HTTP Request: POST /experiences/{id}/attach (link to product)
    ↓
Function: Save external_identifier to dedupe store
    ↓
(Optional) Notify Telegram/Slack/Email
    ↓
Loop back to SplitInBatches
```

---

## Deduplication Strategy for Whop

**Use `external_identifier` field on Product:**
- Set to `sha256(feed_item_link)[:16]` or `feed_item_guid`
- Before creating, `GET /products?external_identifier=<id>` to check existence
- Or maintain local dedupe store (file/SQLite) with `external_identifier` → `prod_id` mapping

**Why external_identifier?**
- Whop enforces uniqueness on this field
- `GET /products?external_identifier=xxx` returns existing product if present
- Enables idempotent re-runs

---

## Error Handling Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid/expired API key | Rotate key in Whop dashboard → update n8n credential |
| `403 Forbidden` | Wrong key type (App vs Account) | Use Account API key for product management |
| `422 Unprocessable` | Validation error (title too long, missing company_id) | Check response body `detail` array |
| `429 Too Many Requests` | Rate limit | Add `Wait` node (1-2s) between API calls |
| `500` | Whop internal error | Retry with exponential backoff |

---

## n8n Credential Setup

**Generic Credential Type: HTTP Header Auth**
- Name: `Whop API`
- Header Name: `Authorization`
- Header Value: `Bearer {{ $credentials.whopApiKey }}`
- Add separate credential field: `whopApiKey` (type: string, required)

**In HTTP Request nodes:**
- Authentication: `Whop API` (select the credential)
- Base URL: `https://api.whop.com/api/v1`

---

## Rate Limits
- **Default**: 100 requests/minute per API key
- **Burst**: Short bursts allowed
- **Best practice**: Add 1-2 second Wait node between mutations (POST)

---

## Testing Checklist

- [ ] Create test product via API (manual curl)
- [ ] Verify product appears in Whop dashboard
- [ ] Create plan → verify pricing
- [ ] Create experience (Files app) → upload test file
- [ ] Attach experience to product
- [ ] Test checkout flow (Whop provides test mode)
- [ ] Verify webhook receives `payment.succeeded` → membership.activated

---

## References
- Whop API Docs: https://docs.whop.com/developer/api/reference
- Whop SDK (TypeScript/Python/Ruby): https://github.com/whopio/whop-sdk
- Sandbox environment: https://dashboard.whop.com (switch to Sandbox mode)