# Novamira tirith-install Cleanup Reference

## Problem
Novamira WordPress plugin (Gutenberg ability) creates temporary directories in `/tmp` named `tirith-install-*` during its operations. Each directory is ~8.5MB. Over time, thousands accumulate (1500+ observed), consuming 15GB+ disk space.

## Root Cause
The Novamira plugin's Gutenberg ability (headless block editor finalization) creates temporary working directories in `/tmp` but doesn't clean them up properly. These accumulate over days/weeks.

## Symptoms
- Disk usage 99% (`df -h /` shows 99%)
- `/tmp` shows 15GB+ usage (`du -sh /tmp`)
- Hundreds of directories like `/tmp/tirith-install-xyz123`

## Immediate Fix
```bash
# Remove all tirith-install directories
rm -rf /tmp/tirith-install-*

# Verify cleanup
du -sh /tmp
```

## Automated Cleanup (Cron)
Add to root crontab (`crontab -e`):

```bash
# Daily cleanup of tirith-install dirs older than 1 day
0 3 * * * find /tmp -name "tirith-install-*" -type d -mtime +1 -exec rm -rf {} \; 2>/dev/null

# Weekly cleanup of old WP backups (All-in-One WP Migration)
0 4 * * 0 find /www/wwwroot/*/wp-content/ai1wm-backups -type f -mtime +30 -delete 2>/dev/null

# Monthly cleanup of aaPanel logs
0 5 1 * * find /www/server/panel/logs -name "*.log" -mtime +30 -delete 2>/dev/null

# Monthly cleanup of Hermes logs (if using Hermes)
0 6 1 * * rm -rf /root/.hermes/logs/* 2>/dev/null
```

## Session Cleanup (Sep 2026)
In this session, cleaned up:
- `/root/.hermes/logs/*` — **1.1GB** freed
- `/www/server/data/mysql-slow.log` — 53MB rotated
- `/www/wwwlogs/*.log` >30 days — ~100MB freed
- `/www/backup/panel/` old backups — 9 files (~400MB) freed
- Docker unused — minimal

**Total freed: ~1.7GB+** (disk 86% → 84%)

## Plugin Details
- **Plugin**: Novamira (WordPress AI plugin)
- **File creating dirs**: `/wp-content/plugins/novamira/includes/abilities/gutenberg/` (Gutenberg bootstrap)
- **Sandbox loader**: `/wp-content/plugins/novamira/includes/sandbox-loader.php` (loads sandbox PHP files)
- **Config**: `NOVAMIRA_SANDBOX_DIR` defined in `novamira.php` → `WP_CONTENT_DIR . '/novamira-sandbox/'`

## Workarounds
1. **Disable Gutenberg ability** in Novamira admin panel if not used
2. **Disable abilities entirely** if AI features not needed: `novamira_is_enabled()` returns false
3. **Monitor `/tmp` weekly**: `du -sh /tmp` — should stay under 100MB

## Files to Monitor
| Path | Purpose |
|------|---------|
| `/tmp/tirith-install-*` | Temp dirs (CLEANUP TARGET) |
| `/www/wwwroot/*/wp-content/novamira-sandbox/` | Sandbox PHP plugins |
| `/wp-content/plugins/novamira/includes/abilities/gutenberg/bootstrap.php` | Gutenberg finalization logic |

## Version Note
Observed in Novamira plugin v1.x (2026). Check if newer versions fix the cleanup bug.