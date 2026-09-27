#!/bin/bash
# /root/backup_db.sh
# Daily MySQL backup script with Telegram notification

DATE=$(date +%F_%H-%M)
BACKUP_DIR="/root/backups"
mkdir -p ${BACKUP_DIR}

# Backup all databases
mysqldump -u root -pRootPass123!@# --all-databases --single-transaction --routines --triggers 2>/dev/null | gzip > ${BACKUP_DIR}/all_dbs_${DATE}.sql.gz

# Keep only last 7 days
find ${BACKUP_DIR} -name "all_dbs_*.sql.gz" -mtime +7 -delete

# Notify via Telegram
/root/telegram_notify.sh "✅ *Backup Database Selesai*
📅 $(date)
📦 File: all_dbs_${DATE}.sql.gz
💾 Size: $(du -h ${BACKUP_DIR}/all_dbs_${DATE}.sql.gz | cut -f1)
📂 Lokasi: ${BACKUP_DIR}/"