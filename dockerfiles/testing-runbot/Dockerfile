FROM laslabs/runbot
MAINTAINER LasLabs Inc <support@laslabs.com>

VOLUME /home/odoo/.ssh
USER root

RUN apt-get update && \
    apt-get install -y python3-matplotlib poppler-utils python3-vatnumber libsasl2-dev \
                        python3-mock graphviz python3-tz python3-unittest2 python3-openid \
                        python3-psycopg2 python3-lxml python3-dev python3-jinja2 python3-yaml \
                        gcc python3-reportlab-accel python3-decorator python3-werkzeug python3-openssl \
                        ant-contrib libldap2-dev python3-gevent python3-setuptools python3-passlib python \
                        lptools python3-simplejson python3-feedparser python3-docutils python3-dateutil wget python3-pyparsing bzr \
                        ghostscript python3-psutil mc python3-pip python3-babel python3-requests python3-pydot python3-pil python3-mako \
                        antiword python3-paramiko make python3-reportlab sudo node-less curl python3-html2text python-matplotlib \
                        emacs-nox git net-tools tree python-pip file nginx python-dev sudo htop locales locales-all wget fonts-dejavu
                        
USER odoo
# Metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="LasLabs.com Runbot v9" \
      org.label-schema.description="Provides a Dockerized Runbot." \
      org.label-schema.url="https://laslabs.com/" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/LasLabs/docker-runbot" \
      org.label-schema.vendor="LasLabs Inc." \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"