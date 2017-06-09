#!/bin/bash
docker build . -t kdvn/odoo10 $1
docker push kdvn/odoo10
