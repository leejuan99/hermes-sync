# n8n Volume Data Recovery

## Problem
When recreating n8n container, if new volume created, old data remains in anonymous volume.

## Identify Volumes
```bash
docker volume ls
# Look for anonymous volume (random hash name) created around original n8n install date
# And named volume (n8n_data) created during latest recreate
```

## Inspect Volumes
```bash
docker volume inspect <old_volume_hash>
docker volume inspect n8n_data
# Note Mountpoint paths
```

## Recovery Steps
```bash
# 1. Stop new container
docker stop n8n && docker rm n8n

# 2. Fix permissions on new volume (n8n runs as node user UID 1000)
chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data

# 3. Copy data from old to new
cp -r /var/lib/docker/volumes/<old_volume_hash>/_data/* /var/lib/docker/volumes/n8n_data/_data/

# 4. Fix permissions again
chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data

# 5. Recreate container with named volume
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
```

## Critical Files to Preserve
- `database.sqlite` - Main database (users, workflows, credentials)
- `database.sqlite-shm` / `database.sqlite-wal` - SQLite WAL files
- `config` - Encryption key
- `storage/` - Binary data
- `nodes/` - Custom nodes

## User Auth Recovery (if broken)
```bash
# Check user table
sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite 'SELECT id, email, roleSlug FROM user;'

# Check auth_identity
sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite 'SELECT * FROM auth_identity;'

# Check project
sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite 'SELECT * FROM project;'

# If missing project for user:
sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite 'INSERT INTO project (id, name, type, creatorId, createdAt, updatedAt) VALUES ("<user_id>", "Personal Project", "personal", "<user_id>", datetime("now"), datetime("now"));'

# Then reset
docker exec n8n n8n user-management:reset
```

## Verify
```bash
docker logs n8n --tail 20
# Should show: "Editor is now accessible via: http://localhost:5678"
```