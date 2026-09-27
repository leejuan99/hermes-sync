#!/bin/bash
# /root/health_check.sh
# Server health check with Telegram notification

CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8"%"}')
RAM_USED=$(free -h | awk '/Mem:/ {print $3}')
RAM_TOTAL=$(free -h | awk '/Mem:/ {print $2}')
DISK=$(df -h / | awk 'NR==2 {print $5}')
DOCKER=$(docker ps --format '{{.Names}}: {{.Status}}' | paste -sd ',' -)
UPTIME=$(uptime -p)

MSG="📊 *Server Health Check*
⏰ $(date)
⏱ Uptime: ${UPTIME}
🖥 CPU: ${CPU}
🧠 RAM: ${RAM_USED} / ${RAM_TOTAL}
💾 Disk: ${DISK} used
🐳 Docker: ${DOCKER}"

/root/telegram_notify.sh "${MSG}"