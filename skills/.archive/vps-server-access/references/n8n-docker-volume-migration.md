# n8n Docker Volume Migration & User Recovery

## Context
When updating n8n via `docker pull n8nio/n8n:latest` and recreating the container, a new anonymous volume was created instead of reusing the existing data volume. This caused loss of workflows, credentials, and users.

## Root Cause
The original n8n container used an **anonymous volume** (long hash name like `db59cd31ec69413fdbf96562ce2c753cc5f23f442624db5a1717a57176ec5892`) instead of the named volume `n8n_data`. When the container was recreated with `-v n8n_data:/home/node/.n8n`, it mounted the empty named volume.

## Migration Procedure

### 1. Identify Volumes
```bash
docker volume ls
# Find the old anonymous volume (long hash) and new n8n_data
```

### 2. Inspect Volume Details
```bash
docker volume inspect OLD_VOLUME_NAME
docker volume inspect n8n_data
```

### 3. Copy Data & Fix Permissions
```bash
# Stop container
docker stop n8n && docker rm n8n

# Copy all data from old to new volume
cp -r /var/lib/docker/volumes/OLD_VOLUME/_data/* /var/lib/docker/volumes/n8n_data/_data/

# Fix permissions (n8n runs as UID 1000 'node' user)
chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data

# CRITICAL: Copy encryption key config
cp /var/lib/docker/volumes/OLD_VOLUME/_data/config /var/lib/docker/volumes/n8n_data/_data/config
```

### 4. Restart with Named Volume
```bash
docker run -d --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

## User Recovery (If Users Lost)

### Check Old DB for Users
```bash
sqlite3 /var/lib/docker/volumes/OLD_VOLUME/_data/database.sqlite "SELECT id, email, roleSlug FROM user;"
```

### Recreate User in New DB
```bash
OLD_USER_ID="7cf4b368-b2ec-4115-806b-608f55a575ad"

sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite "
DELETE FROM user WHERE id='$OLD_USER_ID';
DELETE FROM project WHERE creatorId='$OLD_USER_ID';
INSERT INTO user (id, email, firstName, lastName, password, createdAt, updatedAt, settings, disabled, mfaEnabled, roleSlug)
VALUES ('$OLD_USER_ID', '', '', '', '', '2026-05-29 00:35:17.714', '2026-05-29 00:35:17.714', '{\"userActivated\":false}', 0, 0, 'global:owner');
INSERT INTO auth_identity (userId, providerId, providerType) VALUES ('$OLD_USER_ID', '$OLD_USER_ID', 'email');
"
```

### Verify Recovery
```bash
sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite "SELECT id, email, roleSlug FROM user;"
sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite "SELECT * FROM auth_identity;"
```

## Key Files in n8n Volume
| File | Purpose |
|------|---------|
| `database.sqlite` | Main DB (workflows, users, credentials, projects) |
| `database.sqlite-wal` / `-shm` | WAL mode files (copy these too) |
| `config` | Encryption key for credentials (`{"encryptionKey":"..."}`) |
| `storage/` | Binary data, file uploads |
| `nodes/` | Custom nodes |

## Prevention
- Always use **named volumes** (`-v n8n_data:/home/node/.n8n`) from the start
- Backup `database.sqlite` + `config` before major updates
- Document volume names in deployment notes

## Troubleshooting
| Issue | Fix |
|-------|-----|
| `EACCES: permission denied` on config | `chown -R 1000:1000 /var/lib/docker/volumes/n8n_data/_data` |
| Credentials won't decrypt | Encryption key mismatch — ensure `config` file copied from old volume |
| Users missing after restart | `auth_identity` table empty — re-insert user + auth_identity records |
| Python task runner warnings | Non-fatal — n8n runs fine without Python (for JS tasks only) |