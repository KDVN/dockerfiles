#!/bin/bash
if [ ! -z $AUTH ]; then
  AUTH="--auth $AUTH"
fi

exec nodejs server.js $AUTH --port 80 -w /mnt/extra-addons

exit 1
