#!/bin/bash
if [ ! -z $AUTH ]; then
  AUTH="--auth $AUTH --listen 0.0.0.0"
fi


exec nodejs server.js $AUTH --port 3000 -w /opt/workspace/

exit 1
