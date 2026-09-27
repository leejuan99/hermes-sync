#!/bin/bash
# Backup all MySQL databases
# Requires: MySQL root password in ~/.my.cnf or passed via env

DATE=$(date +%F_%H-%M)
BACKUP_DIR="/root/backups"
mkdir -p ${BACKUP_DIR}

# Dump all databases
mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" --all-databases \
  --single-transaction --routines --triggers 2>/dev/null \
  | gzip > ${BACKUP_DIR}/all_dbs_${DATE}.sql.gz

# Keep only last 7 days
find ${BACKUP_DIR} -name "all_dbs_*.sql.gz" -mtime +7 -delete

# Notify (requires telegram_notify.sh in PATH)
if command -v telegram_notify.sh &> /dev/null; then
  telegram_notify.sh "✅ *Backup Database Selesai*
📅 $(date)
📦 File: all_dbs_${DATE}.sql.gz
💾 Size: $(du -h ${BACKUP_DIR}/all_dbs_${DATE}.sql.gz | cut -f1)
📂 Lokasi: ${BACKUP_DIR}/"
fi