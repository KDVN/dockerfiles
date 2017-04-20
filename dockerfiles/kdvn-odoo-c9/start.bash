#!/bin/bash
touch pidfile
cat pidfile | xargs kill
#odoo --pidfile=./pidfile --logfile=openerp.log &
start-stop-daemon --exec /bin/odoo --start --pidfile pidfile -b -m
