# aaPanel 500 Error Debugging Reference

## Session: 2026-09-01 - Member Site 500 Error

### Problem
`member.smartmillionaire.co.id` returning 500 Internal Server Error while `smartmillionaire.co.id` works fine (200 OK).

### Root Cause Found
**LSAPI_CHILDREN limit reached** - OpenLiteSpeed's LSAPI_CHILDREN limit was set to 20, but the member site's WordPress was spawning more PHP processes (hitting 26+ concurrent).

**Error in stderr.log:**
```
[UID:1000][18696] Reached max children process limit: 20, extra: 6, current: 26, busy: -1, please increase LSAPI_CHILDREN.
```

### Solution Applied
1. **Increased LSAPI_CHILDREN and maxConns** from 20 to 100 for member site vhost:
   ```bash
   sed -i 's/LSAPI_CHILDREN=50/LSAPI_CHILDREN=100/' /www/server/panel/vhost/openlitespeed/detail/member.smartmillionaire.co.id.conf
   sed -i 's/maxConns                50/maxConns                100/' /www/server/panel/vhost/openlitespeed/detail/member.smartmillionaire.co.id.conf
   ```

2. **Killed stuck LSPHP processes:**
   ```bash
   pkill -9 -f 'lsphp.*member'
   ```

3. **Restarted OpenLiteSpeed:**
   ```bash
   /www/server/panel/init.sh restart
   ```

### Verification
```bash
# Test member site
curl -k -s -L -o /dev/null -w '%{http_code}' \
  -H 'Host: member.smartmillionaire.co.id' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  https://localhost/

# Expected: 200 OK
```

### Applied to All Sites
Applied same fix to all sites to prevent future issues:
- `smartmillionaire.co.id`
- `member.smartmillionaire.co.id`
- `leejuan.com`
- `sewapacar.com`
- `crm.smartmillionaire.co.id`

### Key Config Changes
**File:** `/www/server/panel/vhost/openlitespeed/detail/<site>.conf`

```diff
 extprocessor member.smartmillionaire.co.id {
   type                    lsapi
   address                 UDS://tmp/lshttpd/member.smartmillionaire.co.id.sock
   maxConns                100
   env                     LSAPI_CHILDREN=100
   initTimeout             600
   ...
 }
```

### Monitoring
Check stderr.log for LSAPI_CHILDREN warnings:
```bash
tail -f /usr/local/lsws/logs/stderr.log | grep -i 'LSAPI_CHILDREN\|Reached max'
```

### WordPress Specific
The member site has 403 tables and uses multiple plugins (Fluent CRM, Fluent Form, Bit Social, Elementor, etc.) which spawn many concurrent PHP processes during page loads, especially with admin-ajax.php calls from admin dashboard.

### Prevention
1. Set LSAPI_CHILDREN ≥ 50 for WordPress sites with heavy plugins
2. Monitor stderr.log for "Reached max children process limit"
3. Consider caching (LiteSpeed Cache, Redis) to reduce PHP process spawns
4. Set `LSAPI_CHILDREN=100` and `maxConns=100` as default for new WordPress sites