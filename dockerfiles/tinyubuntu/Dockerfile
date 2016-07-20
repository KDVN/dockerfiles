FROM ubuntu
RUN sed -i 's/archive.ubuntu.com/ubuntutym.u-toyama.ac.jp/g' /etc/apt/sources.list && apt-get -y update && apt-get install -y build-essential && apt-get install -y software-properties-common 
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y && apt-get install -y python-pip libldap2-dev libsasl2-dev python-libxslt1 python-webdav python-lxml python-mako python-dateutil python-psycopg2 python-pychart python-pydot python-tz python-reportlab python-yaml python-vobject python python-dev build-essential python-setuptools python-pip python-babel python-mock python-docutils python-Jinja2 python3-jinja2 libldap2-dev libsasl2-dev wget python-simplejson python-werkzeug python-openid oracle-java8-installer python-webdav ant-contrib && easy_install -U unittest2
RUN apt-get -y remove software-properties-common && apt-get autoremove -y && apt-get autoclean -y
RUN rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer
  
# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle
