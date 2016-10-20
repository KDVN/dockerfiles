#!/bin/bash
if [ ! -z $AUTH ]; then
  AUTH="--auth $AUTH --listen 0.0.0.0"
fi

exec nodejs server.js $AUTH --port 80 -w /mnt/extra-addons

exit 1
