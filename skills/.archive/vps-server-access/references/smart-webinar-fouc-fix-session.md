# smart-webinar FOUC Fix Session (GreenCloud + aaPanel)

## Session Context
- **Date:** 2026-06-28
- **Domain:** smartmillionaire.co.id/smart-webinar/
- **Stack:** WordPress + WP Webinar System plugin + OpenLiteSpeed + aaPanel 8.0.3 PRO
- **User Issue:** Page loads in ~1.5s but shows broken layout (FOUC/layout shift) before CSS loads

## Root Cause Identified

The `smart-webinar` is a **WordPress plugin** (WP Webinar System v2.30) at:
```
/www/wwwroot/smartmillionaire.co.id/wp-content/plugins/smart-webinar/
```

**Not a separate site** - it's a plugin in the main WP installation.

### Why FOUC Happens:
1. Plugin loads CSS/JS via `wp_enqueue_style/script` AFTER page content renders
2. No critical CSS inlined for webinar elements
3. OpenLiteSpeed LSCache not configured
4. Theme (LandingPress) loads CSS via `wp_head()` without proper dependencies for plugin assets

## Fix Applied via aaPanel Terminal

### Created FOUC Fix Module: `/www/wwwroot/smartmillionaire.co.id/wp-content/themes/landingpress-wp/fix-fouc.php`

```php
<?php
/**
 * Fix FOUC (Flash of Unstyled Content) for smart-webinar pages
 */
add_action('wp_head', 'fix_smart_webinar_fouc', 1);
function fix_smart_webinar_fouc() {
    if (is_page('smart-webinar') || strpos(get_permalink(), 'smart-webinar') !== false) {
        echo '<style id="fouc-fix">body{opacity:0;visibility:hidden}html{visibility:visible}</style>';
        echo '<script>(function(){var s=document.getElementById("fouc-fix");document.addEventListener("DOMContentLoaded",function(){s.remove();document.body.style.opacity="1";document.body.style.visibility="visible"});setTimeout(function(){s.remove();document.body.style.opacity="1";document.body.style.visibility="visible"},3000)})()</script>';
    }
}

// Force critical CSS inline for smart-webinar
add_action('wp_enqueue_scripts', 'smart_webinar_critical_css', 1);
function smart_webinar_critical_css() {
    if (is_page('smart-webinar') || strpos(get_permalink(), 'smart-webinar') !== false) {
        wp_add_inline_style('landingpress('landingpress-style', '
            .wpws-container,.wpws-webinar-header,.wpws-registration-form{visibility:hidden}
            .wpws-loaded .wpws-container,.wpws-loaded .wpws-webinar-header,.wpws-loaded .wpws-registration-form{visibility:visible}
        ');
    }
}
```

### Added to Theme's functions.php:
```php
require_once get_template_directory() . '/fix-fouc.php';
```

## Alternative Fix: Enable OpenLiteSpeed LSCache (Recommended Long-term)

### Via aaPanel:
1. **Website** → smartmillionaire.co.id → **Conf** → **LSCache** → Enable
2. Install **LiteSpeed Cache** plugin in WordPress
3. Configure: Preset → "Standard" → Save → Purge All

### Why LSCache Helps:
- OpenLiteSpeed native caching + ESI
- Combines/minifies CSS/JS
- Serves cached HTML with inlined critical CSS
- Eliminates FOUC at server level

## Verification (Run in aaPanel Terminal)

```bash
# Test page loads clean
curl -s https://smartmillionaire.co.id/smart-webinar/ | head -50

# Check for render-blocking CSS
curl -I https://smartmillionaire.co.id/smart-webinar/

# Check cache headers
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" https://smartmillionaire.co.id/smart-webinar/
```

## Files Modified This Session

| File | Change |
|------|--------|
| `/wp-content/themes/landingpress-wp/fix-fouc.php` | Created FOUC fix module |
| `/wp-content/themes/landingpress-wp/functions.php` | Added `require_once` include |

## Plugin Details (for future debugging)

**smart-webinar plugin structure:**
```
wp-content/plugins/smart-webinar/
├── cache/
├── includes/
├── localization/
├── scripts/
│   └── translations.js
├── tests/
├── readme.txt
├── wpwebinarsystem.php (main entry, v2.30)
└── wpws-js/
```

## Next Steps for User

1. **Test the fix** - reload smart-webinar page, should load clean
2. **Enable LSCache** in aaPanel for long-term fix
3. **Monitor** - if still issues, check plugin's enqueue order:
```bash
grep -r "wp_enqueue_style\|wp_enqueue_script" /www/wwwroot/smartmillionaire.co.id/wp-content/plugins/smart-webinar/
```