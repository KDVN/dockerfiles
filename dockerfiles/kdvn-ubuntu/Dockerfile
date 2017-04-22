FROM ubuntu
RUN sed -i 's/archive.ubuntu.com/ubuntutym.u-toyama.ac.jp/g' /etc/apt/sources.list && apt-get -y update && apt-get install -y build-essential
RUN apt-get update && apt-get install -y build-essential python-matplotlib poppler-utils python-vatnumber libsasl2-dev python-mock graphviz python-tz python-unittest2 \
                    python-openid python-psycopg2 python-lxml python-xlwt python-dev python-ldap python-jinja2 python-yaml gcc python-libxslt1 \
                    python-reportlab-accel python-decorator python-pybabel python-werkzeug python-openssl ant-contrib libldap2-dev python-gevent \
                    python-vobject python-setuptools python-passlib python lptools python-simplejson python-feedparser python-webdav python-zsi \
                    python-docutils python-egenix-mxdatetime python-dateutil wget python-pyparsing python-pdftools python-gdata bzr ghostscript python-psutil mc python-pip python-pypdf python-pychart python-babel python-requests python-pydot \
                    python-imaging python-mako antiword python-paramiko make python-reportlab sudo node-less curl && easy_install -U unittest2
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
RUN apt-get install nodejs
RUN apt-get dist-upgrade -y

RUN apt-get -y remove && apt-get autoclean -y
RUN rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer
  
# Define commonly used JAVA_HOME variable
