#!/bin/bash
USER_ID=${LOCAL_USER_ID}

#echo "Starting with UID : $USER_ID:-9001"
#sudo usermod -u $USER_ID odoo
#set -e
# set odoo database host, port, user and password
: ${PGHOST:=$PGHOST}
: ${PGPORT:=$DB_PORT_5432_TCP_PORT}
: ${PGUSER:=${DB_ENV_POSTGRES_USER:='postgres'}}
: ${PGPASSWORD:=$PGPASSWORD}
export PGHOST PGPORT PGUSER PGPASSWORD

case "$1" in
	--)
		shift
		exec odoo.py "$@"
		;;
	-*)
		exec odoo.py "$@"
		;;
	*)
		exec "$@"
esac

exit 1
