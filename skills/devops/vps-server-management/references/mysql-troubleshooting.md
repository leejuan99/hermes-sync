# MySQL/MariaDB Troubleshooting Reference

## Crashed Tables

### Symptoms
- "Table './database/table' is marked as crashed and should be repaired"
- "Error establishing a database connection" for WordPress
- 500 errors on specific sites

### Diagnosis
```bash
# Check MySQL error log
tail -100 /www/server/data/*.err

# Check specific table
mysqlcheck -c <database>

# Check all databases
mysqlcheck --all-databases
```

### Fix: REPAIR TABLE
```bash
# Repair single table
mysql -e "REPAIR TABLE <database>.<table>;"

# Repair all tables in database
mysqlcheck -r <database>

# Repair all databases
mysqlcheck -r --all-databases
```

### Example from session
```bash
# Member site DB crashed
mysql -e "REPAIR TABLE thegamec_wp632.wplo_options;"
```

## MySQL Socket Mismatch

### Symptoms
- PHP can't connect to MySQL: "Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock'"
- WordPress "Error establishing a database connection"
- MySQL runs but PHP can't find socket

### Root Cause
MariaDB uses `/tmp/mysql.sock` but PHP/OpenLiteSpeed looks for socket at `/var/run/mysqld/mysqld.sock`

### Fix: Create Symlink
```bash
mkdir -p /var/run/mysqld
ln -sf /tmp/mysql.sock /var/run/mysqld/mysqld.sock
chown mysql:mysql /var/run/mysqld/mysqld.sock
```

### Make Permanent (aaPanel)
Add to aaPanel startup or create systemd service:
```bash
# In /etc/rc.local or similar
mkdir -p /var/run/mysqld
ln -sf /tmp/mysql.sock /var/run/mysqld/mysqld.sock
```

## LSAPI_CHILDREN Limit (OpenLiteSpeed + PHP)

### Symptoms
- 500 errors on WordPress sites under load
- "Reached max children process limit" in stderr.log
- `/usr/local/lsws/logs/stderr.log` shows LSAPI_CHILDREN limit reached

### Root Cause
OpenLiteSpeed's LSAPI_CHILDREN limit (default 20) too low for WordPress concurrent requests

### Fix: Increase Limits in Vhost Config
```bash
# Edit vhost config
vim /www/server/panel/vhost/openlitespeed/detail/<site>.conf

# Change these values:
# LSAPI_CHILDREN 20 -> 100
# maxConns 20 -> 100
```

### Apply to All Sites
```bash
# Find all vhost configs
ls /www/server/panel/vhost/openlitespeed/detail/*.conf

# Batch update
for f in /www/server/panel/vhost/openlitespeed/detail/*.conf; do
  sed -i 's/LSAPI_CHILDREN.*/LSAPI_CHILDREN 100/' "$f"
  sed -i 's/maxConns.*/maxConns 100/' "$f"
done

# Restart OpenLiteSpeed
/www/server/panel/init.sh restart
```

## Disk Space & Log Rotation

### MySQL Slow Query Log
```bash
# Rotate slow log
mv /www/server/data/mysql-slow.log /www/server/data/mysql-slow.log.$(date +%Y%m%d)
systemctl reload mysqld  # or: /www/server/panel/init.sh reload
```

### Cron for Auto Rotation
```bash
# Add to crontab
0 2 * * * mv /www/server/data/mysql-slow.log /www/server/data/mysql-slow.log.$(date +%Y%m%d) && systemctl reload mysqld
```

## Commands Quick Reference

| Task | Command |
|------|---------|
| Check MySQL status | `systemctl status mysqld` or `/www/server/panel/init.sh status` |
| Check socket location | `mysqladmin variables | grep socket` |
| Repair all tables | `mysqlcheck -r --all-databases` |
| Check table status | `mysql -e "CHECK TABLE <db>.<table>;"` |
| View error log | `tail -100 /www/server/data/*.err` |
| Restart MySQL | `/www/server/panel/init.sh restart` |
| Create socket symlink | `mkdir -p /var/run/mysqld && ln -sf /tmp/mysql.sock /var/run/mysqld/mysqld.sock` |