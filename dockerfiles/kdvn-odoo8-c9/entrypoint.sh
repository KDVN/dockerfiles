#!/bin/bash
if [ ! -z $AUTH ]; then
  AUTH="--auth $AUTH --listen 0.0.0.0"
fi
if [ ! -z $GIT_EMAIL ]; then
  git config --global user.email "$GIT_EMAIL"
  git config --global user.name "$GIT_NAME"
fi

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback

USER_ID=${LOCAL_USER_ID}

echo "Starting with UID : $USER_ID:-9001"
sudo usermod -u $USER_ID odoo

bash -c 'nodejs server.js $AUTH --port 3000 -w /opt/workspace/; /bin/bash'

exit 1
