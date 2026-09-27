---
name: wordpress-whatsapp-crm-plugin
description: "Build WordPress plugins for WhatsApp CRM/automation — architecture, Meta Cloud API / OneSender integration, WooCommerce/FluentCRM/forms/LMS sync, visual automation builder, REST API, multi-account SaaS patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wordpress, plugin, whatsapp, crm, meta-cloud-api, onesender, automation, woocommerce, fluentcrm, saas]
    homepage: https://github.com/ArnasDon/wacrm
    related_skills: [wordpress-mcp-integration, novamira-mcp-troubleshooting]
---

# WordPress WhatsApp CRM Plugin Development

This skill covers building **native WordPress plugins** that replicate and extend the functionality of standalone WhatsApp CRMs like [wacrm](https://github.com/ArnasDon/wacrm) (Next.js + Supabase) within the WordPress ecosystem.

## When to Use

- Client wants WhatsApp CRM features **inside WordPress** (not separate SaaS)
- Need deep integration with **WooCommerce, FluentCRM, Forms, LMS, Booking plugins**
- Building a **white-label / multi-tenant SaaS** on WordPress (Multisite or single-site multi-account)
- Prefer **PHP/React hybrid** over Node.js for hosting simplicity (runs on any WP host)

## Architecture Overview

### Database (Native `wpdb`)

| Table (prefix `wp_wacrm_`) | Purpose | Key Columns |
|---|---|---|
| `contacts` | WhatsApp contacts synced from WP users, WC orders, forms | `id`, `wp_user_id`, `phone_e164`, `name`, `email`, `avatar`, `tags` (JSON), `custom_fields` (JSON), `source`, `status`, `created_at` |
| `conversations` | Thread per contact | `id`, `contact_id`, `status` (open/pending/closed), `assigned_agent_id`, `last_message_at` |
| `messages` | Individual messages (inbound/outbound) | `id`, `conversation_id`, `direction`, `type` (text/template/image/video/doc/audio), `content` (JSON), `status` (sent/delivered/read/failed), `wa_message_id`, `sent_at` |
| `templates` | Meta-approved message templates | `id`, `name`, `language`, `category`, `components` (JSON), `status`, `wa_template_id` |
| `broadcasts` | Campaign sends | `id`, `name`, `template_id`, `recipients` (JSON), `status`, `sent_count`, `delivered_count`, `read_count`, `created_by`, `scheduled_at` |
| `automations` | Visual flow definitions | `id`, `name`, `trigger` (JSON), `flow_json` (xyflow), `status`, `version` |
| `automation_runs` | Execution instances | `id`, `automation_id`, `contact_id`, `current_node`, `context` (JSON), `status`, `started_at`, `completed_at` |
| `api_keys` | Public REST API keys | `id`, `account_id`, `name`, `key_hash`, `scopes` (JSON), `last_used_at`, `revoked_at` |
| `webhooks` | Outbound webhook endpoints | `id`, `account_id`, `url`, `events` (JSON), `secret`, `is_active`, `failure_count` |

> **Multitenancy**: Single-site multi-account via `account_id` column on all tables + RLS-style `WHERE account_id = get_current_account_id()` in every query. For Multisite, use `site_id` instead.

### WhatsApp Provider Abstraction

```php
interface WhatsAppProvider {
    public function sendText(string $to, string $text): array;
    public function sendTemplate(string $to, string $template, string $lang, array $params): array;
    public function sendMedia(string $to, string $type, string $url, ?string $caption): array;
    public function getTemplates(): array;
    public function verifyWebhook(array $headers, string $body): bool;
    public function parseInbound(array $payload): array; // returns normalized messages
}

// Implementations:
// - MetaCloudAPI (official WhatsApp Business API)
// - OneSenderAPI (Indonesian provider, simpler setup)
// - WATI / Gupshup / etc.
```

**Config**: Admin setting `wacrm_whatsapp_provider` → instantiates correct class.

### Modern WP Plugin Stack

| Layer | Tool | Purpose |
|---|---|---|
| Build | `@wordpress/scripts` | Webpack + Babel + ESLint + Jest + Prettier (zero-config) |
| Admin UI | React + `@wordpress/components` + `@wordpress/data` | Gutenberg-style admin pages |
| Flow Builder | `@xyflow/react` | Same as wacrm — drag-drop automation canvas |
| Drag-Drop | `@dnd-kit/core` | Kanban pipelines, contact lists |
| Charts | `recharts` | Dashboard analytics |
| Queue | **Action Scheduler** (WC core) | Reliable background jobs (broadcast sends, automation steps, webhook retries) |
| Encryption | `openssl_encrypt` (AES-256-GCM) | API keys, WA tokens, webhook secrets |
| Real-time | SSE (PHP `stream`) or **Soketi** (self-hosted Pusher) | Live inbox updates |
| i18n | WP `__()`, `_e()` + `wp i18n make-pot` | Translation ready |

## Core Feature Implementation Patterns

### 1. Contact Sync (WP → CRM)

```php
// Hook into user registration, profile update, WC orders, form submissions
add_action('user_register', 'wacrm_sync_user_to_contact');
add_action('profile_update', 'wacrm_sync_user_to_contact');
add_action('woocommerce_checkout_create_user', 'wacrm_sync_wc_customer');
add_action('fluentform_form_submitted', 'wacrm_sync_fluentform_entry');

function wacrm_sync_user_to_contact($user_id) {
    $user = get_userdata($user_id);
    $phone = get_user_meta($user_id, 'billing_phone', true) 
          ?: get_user_meta($user_id, 'phone', true);
    if (!$phone) return;
    
    $phone_e164 = wacrm_normalize_phone($phone, get_option('wacrm_default_country', 'ID'));
    if (!$phone_e164) return;
    
    $account_id = wacrm_get_current_account_id();
    $wpdb->upsert('wp_wacrm_contacts', [
        'account_id' => $account_id,
        'wp_user_id' => $user_id,
        'phone_e164' => $phone_e164,
        'name' => $user->display_name,
        'email' => $user->user_email,
        'source' => 'wordpress_user',
        'tags' => json_encode(['wp-user', $user->roles[0] ?? 'subscriber']),
    ], ['wp_user_id' => $user_id, 'account_id' => $account_id]);
}
```

### 2. Inbound Webhook Handler (Meta Cloud API)

```php
// REST endpoint: POST /wp-json/wacrm/v1/webhook/whatsapp
register_rest_route('wacrm/v1', '/webhook/whatsapp', [
    'methods' => 'POST',
    'callback' => 'wacrm_handle_whatsapp_webhook',
    'permission_callback' => '__return_true', // verified via HMAC inside
]);

function wacrm_handle_whatsapp_webhook(WP_REST_Request $request) {
    $provider = wacrm_get_whatsapp_provider();
    $secret = get_option('wacrm_wa_webhook_secret');
    
    // Verify HMAC
    $signature = $request->get_header('X-Hub-Signature-256');
    if (!$provider->verifyWebhook(['X-Hub-Signature-256' => $signature], $request->get_body())) {
        return new WP_REST_Response(['error' => 'Invalid signature'], 401);
    }
    
    $messages = $provider->parseInbound($request->get_json_params());
    foreach ($messages as $msg) {
        // Find or create contact
        $contact = wacrm_find_or_create_contact($msg['from'], $msg['profile_name'] ?? '');
        // Find or create conversation
        $conversation = wacrm_find_or_create_conversation($contact->id);
        // Store message
        wacrm_store_message($conversation->id, $msg);
        // Trigger automations
        wacrm_trigger_automations('message.received', $contact->id, $msg);
    }
    return new WP_REST_Response(['status' => 'ok'], 200);
}
```

### 3. Visual Automation Builder (xyflow)

**Flow JSON stored in `automations.flow_json`:**
```json
{
  "nodes": [
    {"id": "1", "type": "trigger", "position": {"x": 100, "y": 100}, "data": {"trigger": "message.received", "filter": {"keyword": "harga"}}},
    {"id": "2", "type": "condition", "position": {"x": 100, "y": 250}, "data": {"field": "contact.tags", "operator": "contains", "value": "vip"}},
    {"id": "3", "type": "action", "position": {"x": -100, "y": 400}, "data": {"action": "send_template", "template": "price_list_vip"}},
    {"id": "4", "type": "action", "position": {"x": 300, "y": 400}, "data": {"action": "send_template", "template": "price_list_regular"}},
    {"id": "5", "type": "action", "position": {"x": 100, "y": 550}, "data": {"action": "add_tag", "tag": "price_inquiry"}}
  ],
  "edges": [
    {"source": "1", "target": "2"},
    {"source": "2", "target": "3", "sourceHandle": "true"},
    {"source": "2", "target": "4", "sourceHandle": "false"},
    {"source": "3", "target": "5"},
    {"source": "4", "target": "5"}
  ]
}
```

**Execution Engine** (runs via Action Scheduler):
```php
function wacrm_run_automation_step($run_id) {
    $run = wacrm_get_automation_run($run_id);
    $automation = wacrm_get_automation($run->automation_id);
    $flow = json_decode($automation->flow_json, true);
    
    $node = wacrm_find_node($flow, $run->current_node);
    $next = wacrm_execute_node($node, $run->context);
    
    if ($next) {
        $run->current_node = $next;
        $run->context = array_merge($run->context, $node_output);
        wacrm_update_automation_run($run);
        // Schedule next step (immediate or delayed)
        if ($node['data']['delay']) {
            as_schedule_single_action(time() + $node['data']['delay'], 'wacrm_run_automation_step', [$run_id]);
        } else {
            as_enqueue_async_action('wacrm_run_automation_step', [$run_id]);
        }
    } else {
        $run->status = 'completed';
        $run->completed_at = current_time('mysql');
        wacrm_update_automation_run($run);
    }
}
```

### 4. Public REST API (v1)

```php
register_rest_route('wacrm/v1', '/messages', [
    'methods' => 'POST',
    'callback' => 'wacrm_api_send_message',
    'permission_callback' => 'wacrm_verify_api_key',
    'args' => [
        'to' => ['required' => true, 'type' => 'string', 'pattern' => '^\+?[1-9]\d{1,14}$'],
        'type' => ['type' => 'string', 'enum' => ['text', 'template', 'image', 'video', 'document', 'audio'], 'default' => 'text'],
        'text' => ['type' => 'string'],
        'template' => ['type' => 'object'],
        'media_url' => ['type' => 'string', 'format' => 'uri'],
    ],
]);

function wacrm_verify_api_key(WP_REST_Request $request) {
    $auth = $request->get_header('Authorization');
    if (!$auth || !str_starts_with($auth, 'Bearer ')) return new WP_Error('unauthorized', 'Missing API key', ['status' => 401]);
    $key = substr($auth, 7);
    $api_key = wacrm_find_api_key($key); // compares hash
    if (!$api_key || $api_key->revoked_at || !in_array('messages:send', json_decode($api_key->scopes, true))) {
        return new WP_Error('forbidden', 'Invalid or insufficient scope', ['status' => 403]);
    }
    $request->set_param('api_account_id', $api_key->account_id);
    return true;
}
```

### 5. Outbound Webhooks with HMAC

```php
function wacrm_deliver_webhook($webhook, $event, $data) {
    $payload = [
        'id' => wp_generate_uuid4(),
        'event' => $event,
        'occurred_at' => gmdate('c'),
        'account_id' => $webhook->account_id,
        'data' => $data,
    ];
    $body = wp_json_encode($payload);
    $timestamp = time();
    $signature = 't=' . $timestamp . ',v1=' . hash_hmac('sha256', $timestamp . '.' . $body, $webhook->secret);
    
    $response = wp_remote_post($webhook->url, [
        'body' => $body,
        'headers' => [
            'Content-Type' => 'application/json',
            'X-Wacrm-Event' => $event,
            'X-Wacrm-Webhook-Id' => $webhook->id,
            'X-Wacrm-Signature' => $signature,
        ],
        'timeout' => 10,
        'redirection' => 0, // no redirects (SSRF protection)
    ]);
    
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) >= 400) {
        $webhook->failure_count++;
        if ($webhook->failure_count >= 10) $webhook->is_active = false;
        wacrm_update_webhook($webhook);
    } else {
        $webhook->failure_count = 0;
        wacrm_update_webhook($webhook);
    }
}
```

## Key Integration Points (WP-Native Advantages)

| Integration | Hook/Filter | Data Flow |
|---|---|---|
| **WooCommerce** | `woocommerce_checkout_create_user`, `woocommerce_order_status_changed` | Order → Contact + Broadcast template (order_confirmed/shipped) |
| **FluentCRM** | `fluentcrm_contact_created`, `fluentcrm_tag_added` | Two-way tag sync, segment ↔ tag mapping |
| **Gravity Forms / WPForms / Fluent Forms** | `gform_after_submission`, `wpforms_process_complete`, `fluentform_form_submitted` | Entry → Contact + trigger automation |
| **TutorLMS / LearnDash / Sensei** | `tutor_course_completed`, `learndash_course_completed` | Course events → WA notification + tag |
| **Amelia / BookingPress / Simply Schedule** | `amelia_booking_confirmed`, `bookingpress_appointment_created` | Appointment reminders H-1, H-0 via template |
| **Paid Memberships Pro / WooCommerce Subscriptions** | `pmpro_after_change_membership_level`, `woocommerce_subscription_status_updated` | Subscription events → WA renewal notices |

## Multi-Account / SaaS Patterns

### Single Site, Multiple Accounts
- Each "Account" = one WhatsApp Business number + team
- Tables have `account_id` column
- Current account determined by: logged-in user's `wacrm_account_id` user meta, or URL param `?account=X`, or subdomain mapping
- Admin UI: Account switcher in top bar

### WordPress Multisite (Network-Activated)
- Each site = one Account
- Tables use `site_id` (blog_id) instead of `account_id`
- Network Admin: global settings, license, updates
- Site Admin: contacts, conversations, automations for their site only

### White-Label Settings
```php
// Options (per account or network-wide)
wacrm_brand_name        // "MyCRM"
wacrm_brand_logo        // attachment ID
wacrm_brand_color       // #3b82f6
wacrm_custom_domain     // crm.client.com (CNAME → WP site)
wacrm_hide_wp_branding  // true/false
wacrm_login_page_custom // custom login template
```

## Admin UI Structure (React)

```
wp-admin/admin.php?page=wacrm
├── Dashboard (analytics charts)
├── Inbox (conversations list + message thread + composer)
├── Contacts (table + detail drawer + tags sidebar)
├── Pipelines (Kanban board per pipeline)
├── Broadcasts (list + create wizard + reports)
├── Automations (list + xyflow visual builder)
├── Templates (Meta template manager)
├── Settings
│   ├── General (provider, default country, timezone)
│   ├── WhatsApp (Meta App ID/Secret, Phone Number ID, Webhook URL)
│   ├── OneSender (API Key, Sender ID)
│   ├── API Keys (create/revoke/scopes)
│   ├── Webhooks (endpoints + events + HMAC secret)
│   ├── Integrations (toggle WC, FluentCRM, Forms, LMS, Booking)
│   ├── Branding (white-label)
│   └── Accounts (if multi-account)
└── Team (invite users, roles: owner/admin/agent/viewer)
```

## Deployment & Hosting

| Target | Notes |
|---|---|
| **Shared Hosting (aaPanel, cPanel, Hostinger, etc.)** | ✅ Works — just PHP + MySQL, no Node.js needed |
| **VPS (Ubuntu + Nginx + PHP-FPM)** | ✅ Best performance — enable OPcache, Redis object cache |
| **WP Engine / Kinsta / Cloudways** | ✅ Managed WP — check PHP version ≥ 8.2, memory limit 256M+ |
| **Docker (Bedrock / Roots)** | ✅ CI/CD friendly — build step runs `npm run build` in plugin |

**Build Command** (runs in CI or local):
```bash
cd wp-content/plugins/wacrm-wp
npm ci && npm run build  # produces assets/js/admin.min.js, assets/css/admin.min.css
```

## Security Checklist

- [ ] All AJAX/REST endpoints: `check_ajax_referer()` or nonce / API key auth
- [ ] All SQL: `$wpdb->prepare()` — **never** string concatenation
- [ ] File uploads: `wp_handle_upload()` + MIME validation + size limit
- [ ] Webhook URLs: block private IPs (RFC1918), localhost, metadata endpoints (SSRF)
- [ ] Encryption keys: `ENCRYPTION_KEY` in `wp-config.php` (not DB), rotate annually
- [ ] Rate limiting: per-API-key (120/min), per-IP on webhook (60/min)
- [ ] Capabilities: `manage_wacrm`, `send_broadcast`, `manage_automations`, `view_analytics` mapped to WP roles
- [ ] Audit log: `wacrm_log_action($user_id, $action, $context)` for sensitive ops

## Performance Guidelines

- **Inbox polling**: Use SSE (Server-Sent Events) instead of AJAX polling — 1 connection vs N requests
- **Large contact lists**: Server-side pagination + virtualized list (react-window)
- **Broadcast sends**: Queue via Action Scheduler, 1 send/second to respect Meta rate limits
- **Automation runs**: Async actions, batch process 50/run
- **Dashboard stats**: Cache with `wp_cache_set()` (5 min TTL), invalidate on relevant events
- **Database indexes**: Composite indexes on `(account_id, status)`, `(account_id, created_at)`, `(contact_id, conversation_id)`

## Testing Strategy

```bash
# Unit tests (PHP)
./vendor/bin/phpunit --testsuite=unit

# Integration tests (WP)
wp scaffold plugin-tests wacrm-wp
./vendor/bin/phpunit --testsuite=integration

# E2E (Playwright)
npm run test:e2e

# Static analysis
npm run lint        # ESLint + Prettier
./vendor/bin/phpstan analyse src/ --level=5
```

## References

- [wacrm (Next.js reference)](https://github.com/ArnasDon/wacrm) — Feature parity target
- [Meta Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [OneSender API Docs](https://onesender.co.id/api-documentation)
- [Action Scheduler](https://actionscheduler.org/) — Background job queue
- [@wordpress/scripts](https://developer.wordpress.org/block-editor/reference-guides/packages/packages-scripts/) — Build tooling
- [@xyflow/react](https://xyflow.com/) — Flow builder (same as wacrm)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [High Performance Order Storage (HPOS)](https://developer.woocommerce.com/docs/hpos/) — For WC order sync

## Pitfalls & Gotchas

| Issue | Prevention |
|---|---|
| Meta webhook verification fails | Use `X-Hub-Signature-256`, raw body, constant-time compare |
| Template rejected by Meta | Validate components client-side before submit; use Meta's preview API |
| Broadcast stuck "sending" | Monitor Action Scheduler queue health; add stalled-job detection cron |
| Automation infinite loop | Max steps per run (100), detect cycles in flow graph |
| Multisite table prefix confusion | Use `$wpdb->base_prefix` for network tables, `$wpdb->prefix` for site tables |
| PHP memory exhausted on large CSV import | Chunked reading (`fgetcsv` + batch insert 500 rows) |
| SSE disconnects on nginx | `proxy_buffering off; proxy_read_timeout 3600;` in nginx config |
| OneSender rate limit (100/min) | Queue with delay, respect `Retry-After` header |

## Related Skills

- **wordpress-mcp-integration** — If using Novamira MCP to manage this plugin's data remotely
- **novamira-mcp-troubleshooting** — If Novamira sandbox pollution blocks MCP tools
- **facebook-marketing-api** — For Meta Business API token management patterns