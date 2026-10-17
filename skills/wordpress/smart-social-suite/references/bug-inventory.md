# Bug inventory — member social posting suite

Verified by live DB checks (re-verify before acting — state shifts). Code-level findings from auditor reports merge into this file as they land.

1. Engine auto-post OFF: `bit_social_auto_post_settings.isEnabled = false`; zero wp-cron events for the engine → composer posts accumulate `status='scheduled'` and never fire (5 rows stuck in `wplo_sm_social_posts`).
2. Quota engine inert: `wplo_bsb_usage` empty (0 rows since deploy); `wplo_bsb_user_plan` has exactly 1 row (plan starter, EXPIRED 2026-07-18) → members effectively have no plan coverage.
3. Business plan knobs are 0-sentinel: `bsb_plans.business` has `max_accounts=0, max_posts_per_month=0` while other plans carry real limits — verify whether bridge treats 0 as unlimited or as blocked; correct whichever is wrong.
4. Platform rejects hotlinked images: FB error 324 'Missing or invalid image file' on unsplash URLs; native-uploaded media publishes fine → media staging gap between composer/clipper and engine.
5. License integrity: licensing option value is a fabricated `SMARTSOCIALPRO-UNLIMITED-LIFETIME-LICENSE` string; a pro license/check transient sits in `wplo_options` with `{error:true,...}` → any upstream revalidation path is a rebrand-wipe risk.
6. SSM v2 options never saved — only `sm_social_db_ver` exists (`sm_social_enabled`, `sm_social_openai_key`, `sm_social_allowed_groups` absent) → SSM v1 dashboard features fail out-of-the-box until configured.
7. `wplo_sm_social_channels` empty; the channel model overlaps `wplo_bit_social_accounts` (engine never reads it) — collapse one model in the merge.
8. Three published member pages coexist (6398 `/social` `[smart_social_media]`, 6048 `[bsb_studio]`, 6380 `[smart_social_content_library]`) — pick survivors in the merge; at most one studio surface stays live.
9. `bsb_studio` shortcode is a bridge-era leftover registered by SSM — verify it reaches a live code path before deleting the page that relies on it.
10. AI creds stored as pseudo-account rows (platform='openrouter') in the accounts table — document where AI keys belong before refactoring that model.

## Code-level findings 2026-10-17 (full audit; reports at scratch\social-audit\reports\{ssm,pro,bsb}-audit.md)

### Security (P0 — fix before member rollout)
- **PRO nonce middleware no-op** (`smart-social-pro/backend/app/HTTP/Middleware/NonceCheckerMiddleware.php:10-17`): misspelled `_ajax_noce` + action `bitflow_noce`, error return commented → always true. Free-side copy is correct; the pro one is what loads.
- **PRO REST routes no capability check** (`HookProvider.php:56-66`: API router built WITHOUT setMiddlewares) → with A1 + fake-license isPro pass, all pro routes callable by any logged-in user.
- **BSB virtual caps self-bypass** (`bridge Membership/MemberCapabilities.php:23-35` grants `manage_options` to role `bsb_member` in bit-social REST context; all guards return early on manage_options) → enforcement dies the moment real members enroll. 0 users hold the role now — fix pre-launch.
- **SSM SSRF** (`ajax_radar_import_media` ~:1702): arbitrary URL → `uploads/sm_repost/`, no whitelist/size cap.
- **SSM unauth AJAX**: 3 radar handlers (~:1057, :1667, :1728) lack is_user_logged_in; scrape XSS via innerHTML/attr-concat (~:5238-5277, :5390, :5423).
- **Addon unprotected**: `custom-template-addon.php` `ssp_schedule_post` no nonce/cap; schedule UI fakes save.

### Functional (BEN)
- `allSchedule()` returns only schedules with live cron events (free ScheduleController:296-302) → event loss hides schedules.
- Composer `account_ids`: JS JSON.stringify vs PHP (array)+intval → always `[0]` into `ScheduleCreator::create`.
- SSM "AI Agent" fake (JS `prompt` vs PHP `topic`; 0 LLM calls; falls back to 7 hardcoded Coway templates; result never renders: `campaign` vs `data.posts`, `agent-queue-list` vs `campaign-queue-list`).
- Dead: random-scheduler button → `smExecuteBulkRandomSchedule()` undefined; vault add/delete docs registered without methods; admin form wipes `sm_social_openai_key`/`ai_image_engine` on save; `getGroupAccounts` reads missing attrib `accountIds`; pro `updateGeneralSettings` empty stub.
- Timezone drift (strtotime/current_time/get_gmt_from_date mix) ±7h; delete/reschedule/bulk-delete orphan `bs_schedule_id` (ghost schedules).
- Update/phone-home: pre_http_request bypass covers only `wp-api.bitapps.pro`; `auth-apps.bitapps.pro` (OAuth creds, FB/IG refresh, GBP secret) NOT blocked; updater could pull ORIGINAL BitApps build if bypass removed; `ps.w.org/bit-social|bit-flow` banner leaks; `_plugin-commons` updater `$pageNow` typo + wrong base name.
- Addon Sejoli gate reads `_sejoli_user_group` but production Sejoli uses plain `user_group` → template group restriction never matches.

### Rejcted auditor claims (do not re-report)
- QuotaRefund hook `bit_social_log_data` EXISTS (free LoggerTrait:19, 4-arg match) — wiring correct; enforcement inert due to virtual-caps bypass instead.
- `media cannot be null` fatals = Sejoli `sejolisa_acquisition_order`, not the suite.
