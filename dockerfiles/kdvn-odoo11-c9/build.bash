#!/bin/bash
docker build . -t kdvn/odoo11 $1
docker push kdvn/odoo11
