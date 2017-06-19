#!/bin/bash
docker build . -t kdvn/odoo9 $1
docker push kdvn/odoo9
