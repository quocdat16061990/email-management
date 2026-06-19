#!/bin/bash
cd /root/10quanlyvoomly/email-management
echo "=== Start Voomly Sync: $(date) ===" >> sync_cron.log
/usr/bin/python3 manage.py sync_voomly >> sync_cron.log 2>&1
echo "=== End Voomly Sync: $(date) ===" >> sync_cron.log
echo "" >> sync_cron.log
