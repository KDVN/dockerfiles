#!/bin/bash
sleep 1
crontab /etc/crontab
smtpFile=/etc/ssmtp/revaliases
echo "root:cron_$HOSTNAME@$DOMAINNAME:$SMTP_SERVER" >> $smtpFile

# avoid race condition when crontab is trying to read the crontab file , but the file is still not closed
sleep 1 

# exec "$@"
exec crond -f -l 8