#!/bin/bash
docker build . -t kdvn/odoo11:production $1
docker push kdvn/odoo11:production
