#!/bin/bash
ant launch > /opt/pentaho_server/pentaho.log 2>&1 &
set -e
# set odoo database host, port, user and password
: ${PGHOST:=$PGHOST}
: ${PGPORT:=$DB_PORT_5432_TCP_PORT}
: ${PGUSER:=${DB_ENV_POSTGRES_USER:='postgres'}}
: ${PGPASSWORD:=$PGPASSWORD}
export PGHOST PGPORT PGUSER PGPASSWORD

case "$1" in
	--)
		shift
		exec openerp-server "$@"
		;;
	-*)
		exec openerp-server "$@"
		;;
	*)
		exec "$@"
esac

exit 1
