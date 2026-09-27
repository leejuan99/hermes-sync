#!/bin/bash
# n8n Docker Volume Migration & Recovery Script
# Run via aaPanel Terminal or SSH
# Usage: ./n8n-volume-recovery.sh [OLD_VOLUME_NAME] [NEW_VOLUME_NAME]

set -euo pipefail

OLD_VOLUME="${1:-}"
NEW_VOLUME="${2:-n8n_data}"

if [[ -z "$OLD_VOLUME" ]]; then
    echo "Usage: $0 <old_volume_name> [new_volume_name]"
    echo "Available volumes:"
    docker volume ls --format "table {{.Name}}\t{{.Driver}}\t{{.CreatedAt}}"
    exit 1
fi

echo "=== n8n Volume Migration: $OLD_VOLUME -> $NEW_VOLUME ==="

# 1. Stop and remove n8n container
echo "Stopping n8n container..."
docker stop n8n 2>/dev/null || true
docker rm n8n 2>/dev/null || true

# 2. Copy data from old to new volume
echo "Copying data from $OLD_VOLUME to $NEW_VOLUME..."
OLD_PATH="/var/lib/docker/volumes/${OLD_VOLUME}/_data"
NEW_PATH="/var/lib/docker/volumes/${NEW_VOLUME}/_data"

if [[ ! -d "$OLD_PATH" ]]; then
    echo "ERROR: Old volume path not found: $OLD_PATH"
    exit 1
fi

mkdir -p "$NEW_PATH"
cp -r "$OLD_PATH"/* "$NEW_PATH"/

# 3. Fix permissions (n8n runs as UID 1000 'node' user)
echo "Fixing permissions..."
chown -R 1000:1000 "$NEW_PATH"

# 4. Verify critical files copied
echo "Verifying critical files..."
for f in config database.sqlite; do
    if [[ -f "$NEW_PATH/$f" ]]; then
        echo "  ✓ $f copied"
    else
        echo "  ⚠ $f MISSING - credentials may not decrypt!"
    fi
done

# 5. Start n8n with new volume
echo "Starting n8n with volume $NEW_VOLUME..."
docker run -d --name n8n \
    -p 5678:5678 \
    -v "${NEW_VOLUME}:/home/node/.n8n" \
    n8nio/n8n:latest

# 6. Wait and verify
echo "Waiting for n8n to start..."
sleep 10

if docker ps | grep -q n8n; then
    echo "✓ n8n container running"
    echo "Logs:"
    docker logs n8n --tail 20
else
    echo "✗ n8n failed to start"
    docker logs n8n --tail 50
    exit 1
fi

echo ""
echo "=== Migration Complete ==="
echo "Test: curl http://localhost:5678"
echo "If users missing, run user recovery (see references/n8n-docker-volume-migration.md)"