# Member Site 500 Error Fix - Session Reference

## Session: 2026-09-01 - Member Site 500 Error + Database Crash

### Problem
`member.smartmillionaire.co.id` returning 500 Internal Server Error while `smartmillionaire.co.id` works fine (200 OK).

### Root Causes Found (Multiple Issues)

#### 1. LSAPI_CHILDREN Limit Reached
**Error in stderr.log:**
```
[UID:1000][18696] Reached max children process limit: 20, extra: 6, current: 26, busy: -1, please increase LSAPI_CHILDREN.
```

**Fix Applied:**
1. Increased LSAPI_CHILDREN and maxConns from 20 to 100 for member site vhost:
   ```bash
   sed -i 's/LSAPI_CHILDREN=50/LSAPI_CHILDREN=100/' /www/server/panel/vhost/openlitespeed/detail/member.smartmillionaire.co.id.conf
   sed -i 's/maxConns                50/maxConns                100/' /www/server/panel/vhost/openlitespeed/detail/member.smartmillionaire.co.id.conf
   ```

2. Killed stuck LSPHP processes:
   ```bash
   pkill -9 -f 'lsphp.*member'
   ```

3. Restarted OpenLiteSpeed:
   ```bash
   /www/server/panel/init.sh restart
   ```

#### 2. Crashed Database Table (`wplo_options`)
**Error in stderr.log:**
```
Table './thegamec_wp632/wplo_options' is marked as crashed and last (automatic?) repair failed
```

**Root Cause:** MyISAM table `wplo_options` crashed due to high load, disk issues, or unclean shutdown. This is the core WordPress options table used heavily by transients and autoload options.

**Fix Applied:**
```bash
mysql -u thegamec_wp632 -p'p1SyK6A2!)' thegamec_wp632 -e "REPAIR TABLE wplo_options;"
```
Result: `thegamec_wp632.wplo_options    repair    status    OK`

**Additional Fix:** Created MySQL socket symlink for PHP CLI:
```bash
mkdir -p /var/run/mysqld
ln -sf /tmp/mysql.sock /var/run/mysqld/mysqld.sock
```

#### 3. `is_spider()` User-Agent Blocking
The `is_spider()` function in `panelDefense.py` blocks requests with suspicious User-Agent (curl, python, etc.), affecting both panel and WordPress site access when testing with curl/python.

**Test with proper User-Agent:**
```bash
curl -k -s -L -o /dev/null -w '%{http_code}' \
  -H 'Host: member.smartmillionaire.co.id' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  https://localhost/
```

### Final Status
All fixes applied, member site now returns **200 OK**.

### Key Config Changes for Member Site
**File:** `/www/server/panel/vhost/openlitespeed/detail/member.smartmillionaire.co.id.conf`
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

### Monitoring Commands
```bash
# Check for LSAPI_CHILDREN warnings
tail -f /usr/local/lsws/logs/stderr.log | grep -i 'LSAPI_CHILDREN\|Reached max'

# Check for database crashes
tail -100 /usr/local/lsws/logs/stderr.log | grep -i "crashed\|repair failed"

# Test member site
curl -k -s -L -o /dev/null -w '%{http_code}' \
  -H 'Host: member.smartmillionaire.co.id' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  https://localhost/

# Test external access
curl -k -s -L -o /dev/null -w '%{http_code}' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  https://member.smartmillionaire.co.id/
```

### Prevention
1. Set LSAPI_CHILDREN ≥ 50 for WordPress sites with heavy plugins
2. Monitor stderr.log for "Reached max children process limit"
3. Set up automated MySQL table checks: `mysqlcheck --auto-repair --all-databases`
4. Monitor disk space - full disk causes table corruption
5. Consider converting MyISAM to InnoDB for crash resistance:
   ```sql
   ALTER TABLE table_name ENGINE=InnoDB;
   ```
5. Set `LSAPI_CHILDREN=100` and `maxConns=100` as default for new WordPress sites