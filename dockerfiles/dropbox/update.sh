#!/bin/bash
rm /root/.dropbox-dist/dropbox-lnx* -rf
cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
/root/.dropbox-dist/dropboxd
exit 1
