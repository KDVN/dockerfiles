#!/bin/bash
docker build . -t arilogistics/odoo11:production $1
docker push arilogistics/odoo11:production
