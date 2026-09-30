# aaPanel WP Toolkit — mechanism & operations

The WP Toolkit manages WordPress installs recorded in the panel DB. It does not discover them by scanning the filesystem, so a perfectly valid WordPress site stays invisible until the DB says otherwise.

## Which sites appear

```python
# /www/server/panel/class_v2/data_v2.py
query = public.S('sites').prefix('').where('project_type = ?', 'WP2').alias('s')
```

Only `project_type = 'WP2'` is listed. `PHP` means invisible.

```bash
cp /www/server/panel/data/default.db /www/server/panel/data/default.db.bak-$(date +%Y%m%d-%H%M%S)
sqlite3 /www/server/panel/data/default.db "UPDATE sites SET project_type='WP2' WHERE id=<id>;"

# every touched site must still serve: 301 (HTTP->HTTPS) or 200
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: <domain>' http://127.0.0.1/
```

## Tables

| Table | Holds |
|-------|-------|
| `sites` | `project_type` (`PHP` \| `WP2`), `path`, `name`, `status` |
| `wordpress_onekey` | one row per install the Toolkit can manage: `s_id` (sites.id), `d_id` (databases.id), `prefix` (WP table prefix), `user`, `pass` (**plaintext**), `site_type` |
| `wp_site_types` | site-type labels (`Default category`, …); filtering by type INNER JOINs `wordpress_onekey` |
| `wordpress_backups` | backups recorded by the WP2 backup path |

`wp_toolkit/wordpress_scan.py::auto_scan()` walks `sites WHERE project_type='WP2'`, one site per 12h, and writes `/www/server/panel/data/wordpress_wp_scan.json`.

## Side effects of flipping a site to WP2

- **Backup engine changes.** `class_v2/panel_backup_v2.py` branches on `project_type`: non-WP2 → plain `tar.gz` of the site directory; WP2 → `wp_toolkit.wpbackup(...).backup_full_get_data()`, recorded in `wordpress_backups` rather than `backup`.
- **Auto-login and type grouping need `wordpress_onekey`.** The list renders without a row; clicking "log in to WP" does not.

## Diagnostics

```bash
# what the panel considers WordPress
sqlite3 -header -column /www/server/panel/data/default.db "SELECT id,name,project_type FROM sites;"

# Toolkit-managed installs and their stored credentials
sqlite3 -header -column /www/server/panel/data/default.db 'SELECT * FROM wordpress_onekey;'

# scan state
cat /www/server/panel/data/wordpress_wp_scan.json
```

A WP admin password is not recoverable from WordPress's own `wp_users` (hash only), so `wordpress_onekey.pass` is the one place a plaintext copy lives — treat reading that table as handling a secret, and rotate the password there if the DB is ever exposed.

## Admin credentials: why `pass` is plaintext, and how to rotate it

`wordpress_onekey.pass` exists so the Toolkit can replay it into wp-admin ("log in to WP"). WordPress stores only a one-way hash in `wp_users.user_pass`, so auto-login cannot be derived from the hash — the plaintext copy **is** the feature, not a defect. Removing it removes auto-login. Never promise a user they can keep one without the other; the honest answer is the trade-off plus the actual exposure bound.

That bound is the file: `/www/server/panel/data/default.db` is `-rw------- root root`. Verify it and say so, instead of implying the secret is gone.

**The stored value must equal the site's real password.** Resetting the password in WordPress (or in the panel UI) without updating this row leaves auto-login silently failing — no error raised, the button just does not log in.

A row can also exist with an empty `pass`: the site lists fine, auto-login does not work until it is filled in.

There is no wp-cli on this box; drive WordPress itself:

```bash
# 1. find the admin user id (per site: its db + table prefix)
mysql -N -e "SELECT ID,user_login FROM <db>.<prefix>users
  WHERE ID IN (SELECT user_id FROM <db>.<prefix>usermeta
               WHERE meta_key='<prefix>capabilities' AND meta_value LIKE '%administrator%');"

# 2. set and verify with the php CLI matching the pool version
cd /www/wwwroot/<site>
/www/server/php/83/bin/php -r "require 'wp-load.php'; wp_set_password('<NEW>', <ID>);"
/www/server/php/83/bin/php -r "require 'wp-load.php'; \$u=get_userdata(<ID>); echo wp_check_password('<NEW>', \$u->user_pass, <ID>) ? 'VALID' : 'INVALID';"

# 3. mirror it into the panel
sqlite3 /www/server/panel/data/default.db "UPDATE wordpress_onekey SET pass='<NEW>' WHERE s_id=<site id>;"
```

Prove the pair actually agrees before reporting success — a rotate that updates only one side looks complete and is not:

```bash
stored=$(sqlite3 /www/server/panel/data/default.db "SELECT pass FROM wordpress_onekey WHERE s_id=<id>;")
cd /www/wwwroot/<site> && /www/server/php/83/bin/php -r \
  "require 'wp-load.php'; \$u=getuserdata(<ID>); echo wp_check_password('${stored}', \$u->user_pass, <ID>) ? 'COCOK' : 'TIDAK COCOK';"
```

`wp_set_password()` invalidates every existing session for that user — warn the user they will be signed out of wp-admin.
