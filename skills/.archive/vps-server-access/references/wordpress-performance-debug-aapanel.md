# WordPress Performance Debugging via aaPanel

Session-specific notes from troubleshooting smartmillionaire.co.id/smart-webinar loading issues.

## The Problem
User reported WordPress page at `https://smartmillionaire.co.id/smart-webinar/` loading slowly ("jeda" / laggy).

## Root Cause Candidates Found

### 1. smart-webinar is a WordPress Plugin
- Located at: `/www/wwwroot/smartmillionaire.co.id/wp-content/plugins/smart-webinar/`
- Not a separate site/subdirectory - it's a plugin in main WP installation
- Check if plugin is:
  - Resource-heavy (large JS/CSS, external API calls)
  - Making synchronous external requests
  - Poorly coded database queries

### 2. OpenLiteSpeed Server
- Smartmillionaire.co.id runs on OpenLiteSpeed 1.8.3 (PHP 8.3)
- LSCache available but may not be configured
- OpenLiteSpeed handles PHP differently than Nginx/Apache

### 3. Potential Bottlenecks
- **Plugins**: Check all plugins in `/wp-content/plugins/`
- **Database**: Check for slow queries, bloated wp_options
- **PHP-FPM**: Check worker config, memory limits
- **OPcache**: May not be optimized for PHP 8.3
- **External resources**: Plugin may load external scripts/styles

## aaPanel Debugging Commands (run in aaPanel Terminal)

```bash
# 1. Check error logs
tail -f /www/wwwlogs/smartmillionaire.co.id.error.log

# 2. Check access logs for slow requests
grep "smart-webinar" /www/wwwlogs/smartmillionaire.co.id.access.log

# 3. Plugin sizes (identify heavy ones)
du -sh /www/wwwroot/smartmillionaire.co.id/wp-content/plugins/*

# 4. Database size and slow queries (via phpMyAdmin in aaPanel Databases)
# - Check wp_options for autoloaded data > 1MB
# - Check postmeta for orphaned entries

# 5. PHP-FPM status
systemctl status php-fpm-83

# 6. OPcache status
php -i | grep opcache

# 7. WordPress cron (wp-cron.php can cause delays)
# Check if real cron is set up in aaPanel Cron
```

## Quick Fixes via aaPanel (No SSH Needed)

### Enable LSCache (OpenLiteSpeed Built-in)
1. **Website** → smartmillionaire.co.id → **Conf**
2. Add cache rules for WordPress
3. Install **LSCache WordPress plugin** (recommended)

### PHP Optimization
1. **Website** → smartmillionaire.co.id → **PHP Version** → 8.3
2. Click **Config** next to PHP version
3. Enable **OPcache**, **JIT** (PHP 8.3+)
4. Increase `memory_limit` to 256M or 512M
5. Set `max_execution_time` = 300

### Database Optimization (via Databases → phpMyAdmin)
1. Select WP database
2. Check tables with overhead → Optimize
3. Check `wp_options` for large autoloaded rows
4. Install **WP-Optimize** plugin if needed

### Plugin Audit
1. **Files** → `/www/wwwroot/smartmillionaire.co.id/wp-content/plugins/`
2. Disable unused plugins (rename folder to `plugin-name-disabled`)
3. Test loading speed after each disable

### External Requests Check
```bash
# Find external domains in plugin files
grep -r "https://" /www/wwwroot/smartmillionaire.co.id/wp-content/plugins/smart-webinar/ --include="*.php" --include="*.js" --include="*.css"
```

## Specific Findings This Session
- smart-webinar plugin exists at `/wp-content/plugins/smart-webinar/`
- Main site: smartmillionaire.co.id (OpenLiteSpeed, PHP 8.3, 4 sites on server)
- Server resources: CPU 18%, RAM 25%, Disk 57% - NOT resource-starved
- aaPanel version 8.0.3 PRO

## Next Steps for User
1. Login to aaPanel → Files → Check smart-webinar plugin size
2. Databases → phpMyAdmin → Check WP database health
3. Website → Conf → Enable LSCache rules
4. Disable smart-webinar temporarily → test speed → if fast, plugin is culprit
5. If plugin needed, audit its code for external requests/slow queries