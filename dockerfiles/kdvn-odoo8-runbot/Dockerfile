#COPY FROM https://raw.githubusercontent.com/it-projects-llc/odoo-runbot-docker/master/Dockerfile
FROM kdvn/ubuntu

USER root

RUN apt-get update && \
    apt-get install -y python3-matplotlib poppler-utils python3-vatnumber libsasl2-dev \
                        python3-mock graphviz python3-tz python3-unittest2 python3-openid \
                        python3-odf python3-xlrd phantomjs \
                        python3-suds \
                        python3-psycopg2 python3-lxml python3-dev python3-jinja2 python3-yaml \
                        gcc python3-reportlab-accel python3-decorator python3-werkzeug python3-openssl \
                        ant-contrib libldap2-dev python3-gevent python3-setuptools python3-passlib python \
                        lptools python3-simplejson python3-feedparser python3-docutils python3-dateutil wget python3-pyparsing bzr \
                        ghostscript python3-psutil mc python3-pip python3-babel python3-requests python3-pydot python3-pil python3-mako \
                        antiword python3-paramiko make python3-reportlab sudo node-less curl python3-html2text python-matplotlib \
                        emacs-nox git net-tools tree python-pip file nginx python-dev sudo htop locales locales-all wget fonts-dejavu
RUN pip install gevent psycogreen && \
    #update werkzeug to make phantomjs work. See http://odoo-development.readthedocs.io/en/latest/dev/tests/js.html#regular-phantom-js-tests
    pip install werkzeug --upgrade && \
    wget -q -O- https://raw.githubusercontent.com/OCA/pylint-odoo/master/requirements.txt | xargs pip install && \
    # Extra package for pylint-odoo plugin
    npm install -g jshint
RUN pip3 install vobject PyPDF2 pypdf xlwt babel ldap num2words

# install phantomjs (based on https://hub.docker.com/r/cmfatih/phantomjs/~/dockerfile/ )
ENV PHANTOMJS_VERSION 1.9.8

RUN \
  apt-get install -y libfreetype6 libfontconfig && \
  mkdir -p /srv/var && \
#   wget -q --no-check-certificate -O /tmp/phantomjs-$PHANTOMJS_VERSION.tar.gz https://github.com/ariya/phantomjs/archive/$PHANTOMJS_VERSION.tar.gz && \
#   tar -xzf /tmp/phantomjs-$PHANTOMJS_VERSION.tar.gz -C /tmp && \
#   rm -f /tmp/phantomjs-$PHANTOMJS_VERSION.tar.gz && \
#   mv /tmp/phantomjs-$PHANTOMJS_VERSION/ /srv/var/phantomjs && \
#   ln -s /srv/var/phantomjs/bin/phantomjs /usr/bin/phantomjs && \
  git clone https://github.com/n1k0/casperjs.git /srv/var/casperjs && \
  ln -s /srv/var/casperjs/bin/casperjs /usr/bin/casperjs && \
  apt-get autoremove -y && \
  apt-get clean all
  

RUN mkdir -p /opt/extra-addons /opt/odoo /opt/odoodata

RUN wget -qO- https://nightly.odoo.com/8.0/nightly/src/odoo_8.0.latest.tar.gz | tar xz -C /opt/odoo/ --strip 1
RUN adduser -u 1000 --system --group --home /home/odoo --shell /bin/bash odoo
RUN chmod a+x /opt/odoo/odoo.py && chmod 775 /opt/extra-addons/ /opt/odoodata -R && chown -R 1000 /opt/extra-addons /home/odoo/ /opt/odoodata

# fix access issue with nginx
RUN touch /var/log/nginx/error.log && \
    touch /var/log/nginx/access.log && \
    chown odoo:odoo -R /var/log/nginx && \
    chown odoo:odoo -R /var/lib/nginx/


ENV BUILD_DATE=2018_Feb_06

RUN git clone -b 8.0 https://github.com/it-projects-llc/runbot-addons.git /mnt/runbot-addons && \
    pip install --upgrade pylint && \
    pip install --upgrade git+https://github.com/oca/pylint-odoo.git && \
    git clone https://github.com/odoo/odoo-extra.git /mnt/odoo-extra && \
    rm -rf /mnt/odoo-extra/website_twitter_wall

# grant access to work dir

RUN chown odoo:odoo -R /mnt/odoo-extra/runbot/static/ && mkdir /etc/odoo

COPY ./odoo.conf /etc/odoo/odoo.conf

RUN true && sed -i "s/if len(db_names) > 1:/if True:/" /opt/odoo/openerp/service/server.py

VOLUME ["/mnt/odoo-extra", "/mnt/runbot-addons", "/opt/workspace","/opt/odoodata","/opt/extra-addons"]
RUN ln -s /opt/odoo/odoo.py /bin/odoo-server

CMD ["odoo-server", "--database=runbot", "--db-filter=^runbot$", "--workers=2","--config=/etc/odoo/odoo.conf"]

USER odoo