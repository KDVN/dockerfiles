FROM ubuntu
RUN sed -i 's/archive.ubuntu.com/ubuntutym.u-toyama.ac.jp/g' /etc/apt/sources.list && apt-get -y update && apt-get install -y build-essential && apt-get install -y software-properties-common 
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y && \
  apt-get install -y build-essential python-matplotlib poppler-utils python-vatnumber libsasl2-dev python-mock graphviz python-tz python-unittest2 \
                    python-openid python-psycopg2 python-lxml python-xlwt python-dev python-ldap python-jinja2 python-yaml gcc python-libxslt1 \
                    python-reportlab-accel python-decorator python-pybabel python-werkzeug python-openssl ant-contrib libldap2-dev python-gevent \
                    python-vobject python-setuptools python-passlib python lptools python-simplejson python-feedparser python-webdav python-zsi \
                    python-docutils python-egenix-mxdatetime python-dateutil wget python-pyparsing python-pdftools python-gdata bzr ghostscript \
                    oracle-java8-installer python-psutil mc python-pip python-pypdf python-pychart python-babel python-requests python-pydot \
                    python-imaging python-mako antiword python-paramiko make python-reportlab && \
 easy_install -U unittest2
RUN apt-get dist-upgrade -y
RUN apt-get install node-less -y
RUN apt-get -y remove software-properties-common && apt-get autoremove -y && apt-get autoclean -y
RUN rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer
  
# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle
