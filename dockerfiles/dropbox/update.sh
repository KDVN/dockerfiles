#!/bin/bash
#rm /root/.dropbox-dist/dropbox-lnx* -rf
#cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
echo fs.inotify.max_user_watches=100000 | tee -a /etc/sysctl.conf; sysctl -p
/root/.dropbox-dist/dropboxd
exit 1
