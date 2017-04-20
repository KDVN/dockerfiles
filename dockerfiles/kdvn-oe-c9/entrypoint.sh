#!/bin/bash
if [ ! -z $AUTH ]; then
  AUTH="--auth $AUTH --listen 0.0.0.0"
fi

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback

USER_ID=${LOCAL_USER_ID:-9001}

echo "Starting with UID : $USER_ID:-9001"
sudo usermod -u $USER_ID devuser

bash -c 'nodejs server.js $AUTH --port 3000 -w /opt/workspace/; /bin/bash'
#exec nodejs server.js $AUTH --port 3000 -w /opt/workspace/

exit 1
