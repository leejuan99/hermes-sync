# Novamira MCP Abilities Reference

Complete list of abilities exposed by the Novamira WordPress plugin via MCP.

## Fluent CRM Abilities (21)

### Contact Management
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/list-contacts` | List/filter contacts with tags + lists inline. Search matches name/email/custom fields. | `per_page` (1-100), `page`, `search`, `status`, `tags`, `lists`, `order_by`, `order` |
| `fluent-crm/get-contact` | Full contact profile (by ID or email). Default: notes, email_history, automations. Optional: activity, purchase_history, support_tickets, ai_summary. | `id` OR `email`, `include` (activity, purchase_history, support_tickets, ai_summary) |
| `fluent-crm/upsert-contact` | Create/update contact by ID or email. Status changes fire native hooks. | `email` (required), `first_name`, `last_name`, `status`, `tags`, `lists`, `custom_fields` |
| `fluent-crm/bulk-upsert-contacts` | Batch create/update up to 500 contacts. Returns per-row results. | `contacts` (array of contact objects), `skip_existing` |
| `fluent-crm/delete-contact` | Hard-delete contact. Optional `delete_emails` wipes email log. | `id` OR `email`, `delete_emails` (bool) |
| `fluent-crm/apply-segments-to-contacts` | Add/remove tags & lists across many contacts. Dry-run first! Cap 5000. | `contact_ids`, `add_tags`, `remove_tags`, `add_lists`, `remove_lists`, `dry_run` |

### Segments & Estimates
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/estimate-dynamic-segment` | Count contacts matching a filter (no rows returned). | `status`, `tags`, `lists`, `search`, `date_range` |
| `fluent-crm/get-crm-context` | Discovery - Returns identity, permissions, stats, top tags/lists, triggers/actions, enums, custom fields schema, default sender. Call once per session. | (none) |

### Campaigns
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/list-campaigns` | List campaigns with stats. Excludes one-off emails by default. | `status`, `per_page`, `page` |
| `fluent-crm/get-campaign` | Campaign details with stats. Optional: A/B subjects, link_report, recipients_estimate. | `id`, `include` (ab_subjects, link_report, recipients_estimate) |
| `fluent-crm/upsert-campaign` | Create/update draft campaign. Recipients = tags + lists only. | `name`, `subject`, `content`, `status`, `tags`, `lists`, `send_at` |
| `fluent-crm/change-campaign-status` | State transitions: schedule, pause/resume, unschedule, delete. | `id`, `status` (draft, scheduled, sending, sent, paused, deleted) |
| `fluent-crm/send-test-email` | Render & send test copy (prefixed "TEST:"). No campaign record. | `campaign_id`, `email` |
| `fluent-crm/send-email-to-contact` | Send one-off email to subscribed/transactional contact. Routes via FluentSMTP. | `contact_id` OR `email`, `subject`, `content` |

### Automations (Funnels)
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/list-automations` | List/filter funnels with subscriber counts. | `status`, `per_page`, `page` |
| `fluent-crm/get-automation` | Funnel details with sequences + per-step report. Email bodies opt-in (`include_bodies=true`). | `id`, `include_bodies` |
| `fluent-crm/list-funnel-subscribers` | List contacts enrolled in a funnel by status. | `funnel_id`, `status`, `per_page`, `page` |
| `fluent-crm/update-contact-automation-status` | Resume, cancel, or advance_now a contact in a funnel. | `contact_id`, `funnel_id`, `action` (resume, cancel, advance_now) |

### Sequences (Drip)
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/list-sequences` | List drip sequences with stats (emails, subscribers, revenue). | `per_page`, `page` |
| `fluent-crm/get-sequence` | Sequence details with emails. Bodies opt-in. | `id`, `include_bodies` |
| `fluent-crm/manage-sequence-subscribers` | Subscribe/unsubscribe contacts to/from a sequence. Dry-run available. Cap 5000. | `sequence_id`, `contact_ids`, `action` (subscribe, unsubscribe), `dry_run` |

### Tags & Lists
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/manage-tag` | Create, update, delete, or merge tags. Destructive on delete/merge. | `action` (create, update, delete, merge), `id`, `title`, `slug`, `merge_into` |
| `fluent-crm/manage-list` | Create, update, delete, or merge lists. Destructive on delete/merge. | `action` (create, update, delete, merge), `id`, `title`, `slug`, `merge_into` |

### Notes
| Ability | Description | Key Parameters |
|---------|-------------|----------------|
| `fluent-crm/add-contact-note` | Add note to contact (types: note, call, email, meeting, quote). HTML supported. | `contact_id`, `note`, `type` |
| `fluent-crm/delete-contact-note` | Delete a single note by ID. | `note_id` |

## Other Novamira Abilities

### Gutenberg/Content
- `gutenberg-get-content`
- `gutenberg-write-content`
- `gutenberg-add-pending-change`
- `gutenberg-enable-batch-finalization`

### File/Code Execution
- `novamira/execute-php` — Execute arbitrary PHP in WordPress context
- `novamira/read-file` — Read file from WordPress filesystem
- `novamira/write-file` — Write file to WordPress filesystem
- `novamira/edit-file` — Edit file (patch-style)
- `novamira/list-directory` — List directory contents

### WP-CLI
- `novamira/run-wp-cli` — Run WP-CLI command
- `novamira/get-wp-cli-job` — Get async WP-CLI job status

### Admin/Utility
- `novamira/create-upload-link` — Generate presigned upload URL
- `novamira/create-admin-access-link` — Generate temporary admin login link

## MCP Tool Calling Pattern

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "mcp-adapter-execute-ability",
    "arguments": {
      "ability_name": "fluent-crm/list-contacts",
      "parameters": {
        "per_page": 100,
        "page": 1,
        "status": "subscribed"
      }
    }
  }
}
```

Response:
```json
{
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\":true,\"data\":{\"items\":[...],\"total\":2287,\"page\":1,\"per_page\":100,\"pages\":23}}"
    }]
  }
}
```

**Note:** The response `text` field contains a double-encoded JSON string. Parse twice:
```python
outer = json.loads(response)
text = outer['result']['content'][0]['text']
data = json.loads(text)  # <-- second parse
items = data['data']['items']
```

## Rate Limits & Best Practices

| Operation | Limit | Recommendation |
|-----------|-------|----------------|
| `list-contacts` | 100/page | Use per_page=100, paginate via `page` |
| `bulk-upsert-contacts` | 500/batch | Split large imports into 500 chunks |
| `apply-segments-to-contacts` | 5000/call | Use dry_run=true first |
| `manage-sequence-subscribers` | 5000/call | Use dry_run=true first |
| `delete-contact` | 1/call | Loop with 500ms delay for bulk |
| `execute-php` | - | Dangerous; use only when necessary |

## Authentication

Credentials passed as environment variables to npx process:
```bash
WP_API_URL=https://site.com/wp-json/mcp/novamira \
WP_API_USERNAME=youruser \
WP_API_PASSWORD=app_password \
npx -y @automattic/mcp-wordpress-remote@latest
```

Application password created in WordPress: Users → Profile → Application Passwords.

## Error Handling

Common errors:
- `401 Unauthorized` — Invalid/expired application password
- `403 Forbidden` — User lacks capability (need `fluent_crm_manage_contacts`)
- `404 Not Found` — Ability name wrong or Novamira not active
- `500 Server Error` — PHP error in ability handler; check WP debug.log
- `timeout` — Increase `mcp_discovery_timeout` in Hermes config