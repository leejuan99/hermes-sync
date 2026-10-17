---
name: smart-social-suite
description: "Use when working on the member-site social posting suite."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
tags: [wordpress, social, sejoli, smartmillionaire]
metadata:
  hermes:
    tags: [wordpress, social, sejoli, smartmillionaire]
    related_skills: [smart-binary-mlm, sejoli, subagent-fanout]
---

# Member-site social posting suite (member.smartmillionaire.co.id)

## When to Use

Any task touching `smart-social-pro`, `smart-social-prok`, `smart-social-media` or `bitsocial-sejoli-bridge`: auditing, bug fixing, publishing pipeline work, member plans/quotas, merging the stack into one plugin.

Scope: plugins `smart-social-pro`, `smart-social-prok`, `smart-social-media`, `bitsocial-sejoli-bridge` — audit, bug fixing, refactor, merge. Same host and access as `smart-binary-mlm` (VPS ssh -p 2222, wp-cli --allow-root, DB prefix `wplo_`). Production FILE edits need a tar backup in /www/wwwroot/backups/ first.

The owner refers to these by syllables (SSM / BSB / 'pro / prok'); map every such name to the directory names above BEFORE working — don't guess the set. `sm-engagement-exchange` (SMEE) is a SEPARATE paid engagement-exchange plugin (points for mutual engagement among members, own 14 tables, inactive/empty): it is NOT part of the posting stack, NOT in merge scope, and must not drift into the social plugins' work — audit it only on explicit request.

## Architecture: one system wearing three plugin hats

- **smart-social-pro** (v1.13.10, text domain `bit-social`) = the ENGINE — commercial BitApps SocialPro bundled + rebranded: namespace `BitApps\SocialPro`, real platform API publishing (FB/IG/Threads/Pinterest/Bluesky/LinkedIn/TikTok/Telegram/Discord/Tumblr/Twitter/GBP; AI via OpenAI/Claude/Gemini/OpenRouter). Bundled `bit-social-free/` folder inside it carries the free-tier app incl. `SideBarMenu.php`. Local addon `custom-template-addon.php` adds CPT 'Template Konten' + shortcode `smart_social_content_library`. Admin is a React/Vue SPA (backend/app/Views + built assets/).
- **bitsocial-sejoli-bridge** (BSB, v0.4.0) = the MEMBERSHIP GATE. Plan/quota enforcement (Enforcement/*), account ownership filters, Sejoli plan registry (option `bsb_plans`: starter/pro/business). Tables `wplo_bsb_ownership/usage/user_plan`.
- **smart-social-media** (SSM, v2.0.0) = the MEMBER COMPOSER. One 6.2k-line file: 1 admin menu (`sm-social-settings`, capability manage_options), shortcodes `smart_social_media` / `sm_social` / `smart_social_studio` / `bsb_studio`, 18 `sm_social_*` AJAX handlers, 3 tables `wplo_sm_social_{posts,channels,vault}`, options `sm_social_{enabled,allowed_groups,openai_key,ai_image_engine,ai_instructions}`.
- **smart-social-prok** = stale duplicate of pro (older code, INACTIVE). Never edit it; archive/delete once confirmed.
- wp-content/smart-social-error.log is pro's runtime fatal trap — but it receives fatals from ALL plugins on the site when loaded; grep by plugin path before attributing.

## Contract surfaces (do not break when merging/refactoring)

- **Composer→engine**: SSM `ajax_save_post` calls `\BSB\Studio\ScheduleCreator::create($account_ids, $templates, $scheduled_gmt, $title)` when `class_exists('BSB\Studio\ScheduleCreator')`, storing the returned id in `sm_social_posts.bs_schedule_id`. Schedule JSON shape: `{settings:{name,started_at,repeat,sleep_days,sleep_time,post_publish_order}, accounts:{accountIds:[],groupIds:[]}, templates:{<platform>:{platform,content,media:[{url}],link,comment,post_mode}}}`.
- **Pages**: 6048 'Smart Social Studio' `[bsb_studio]`, 6380 'Preview Content Library' `[smart_social_content_library]`, 6398 slug `social` `[smart_social_media]` (legacy v1 dashboard).
- **Member plans**: BSB maps Sejoli member group → plan (`wplo_bsb_user_plan` carries expires_at); engine accounts live in `wplo_bit_social_accounts` (`details` JSON incl. access_token cleartext + generates_on epoch). AI credentials are pseudo-account rows (platform='openrouter').

## Live-state checks (run before any work; state shifts)

```
wp option get bit_social_auto_post_settings   # JSON isEnabled — engine auto-post global switch
wp db query "SHOW TABLES LIKE 'wplo_bit_%'"   # engine/bridge tables
wp db query "SELECT id,status,cron_status,last_published_at FROM wplo_bit_social_schedules ORDER BY id DESC LIMIT 5"
wp db query "SELECT platform,COUNT(*) FROM wplo_bit_social_accounts GROUP BY platform"
wp db query "SELECT COUNT(*) FROM wplo_sm_social_posts WHERE status='scheduled'"
wp cron event list --fields=hook --allow-root  # grep bit/social
```

Query gotchas: `usage` is a MariaDB reserved word (backtick/alias it); column sets differ per table (`bit_social_logs` = details/platform/status; `bsb_usage` = period_key/post_count/ai_count) — `SHOW COLUMNS` first. Schedule `status=2` + `cron_status=0` = consumed test run; last response incl. platform error bodies lands in `bit_social_logs.details`.

## Known failure modes (check these first)

- **Composer posts never publish**: they sit `status='scheduled'` in `sm_social_posts` when the engine path is off. Check in order: `bit_social_auto_post_settings.isEnabled`, cron actually running, plan not expired (`bsb_user_plan.expires_at`), account connect not stale.
- **Platform rejects media**: remote hotlinks (unsplash etc.) fail with FB error 324 'Missing or invalid image file'; locally-uploaded media (wp-content/uploads) publishes fine. ANY composer/clipper path must STAGE media into uploads before scheduling — never hand a third-party URL to the platform API directly.
- **Token age**: page token `generates_on` epoch lives in the account row details; re-verify with a real publish attempt before blaming engine code.
- **SSM v1 dead out-of-the-box**: all `sm_social_*` options except `sm_social_db_ver` were never saved → enabled flag/openai key absent. 'Feature exists in code' ≠ 'feature configured' — check the option before reporting broken.
- **Bundle/update integrity**: licensing option holds a fabricated `SMARTSOCIALPRO-*-LICENSE` key; a pro license/check transient carries `{error:true}`. Neutralize Update/Updater + Update/API phone-home so BitApps re-validation can never overwrite the rebrand; keep `bit_social_pro_tracking*` skipped.

## Standing decisions (owner)

- Collapse the suite into ONE host: engine `smart-social-pro` hosts the SSM member features as additional submenus (SSM ships ~11 feature areas: studio/komposer, calendar, AI copilot/caption, AI image, DFY vault, radar, clipper, review queue, channel connection & quota, stats, content library). After the merge, do NOT run SSM's legacy v1 dashboard page (`/social`) in parallel.
- Keep the BSB enforcement layer working as-is (plans/quotas/ownership) — it is the paywall between members and engine accounts.
- Anti-MLM member vocabulary rules from `smart-binary-mlm` apply to all new member-facing surfaces here too.

## Audit / fanout recipe

Tar the plugin dirs on the VPS, scp, extract to a fixed scratch root (this host's git-bash `$TMPDIR` resolves to `/tmp` = C:\Users\pc\AppData\Local\Temp, NOT the hermes scratch dir — helper scripts need explicit /c/... or C:/... paths), then dispatch ONE auditor child per plugin with EXCLUSIVE dir ownership (ssm / pro / bsb); each child writes `<scratch>\social-audit\reports\<x>-audit.md` with file:line evidence, read-only on the VPS. Confirm every auditor claim against code before reporting to the owner; merge accepted findings into `references/bug-inventory.md`, including a 'rejected claims' section for false positives (an auditor did once report a hook as missing when it existed; a states 'the media-cannot-be-null fatal was Sejoli, not the suite').

Verify claims against the copy that ACTUALLY loads: the pro bundle ships duplicate class copies (pro `backend/` namespace `BitApps\SocialPro` vs bundled `bit-social-free/backend/` namespace `BitApps\Social`, e.g. `NonceCheckerMiddleware` exists in both). rglob/`next(rglob)` can return the free copy — open the `backend/` one or you read a shadowed file and wrongly conclude 'the audit claim does not match the code'. Verify at least every P0 claim by opening the file, not by trusting the report's snippet.
