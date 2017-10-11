FROM kdvn/ubuntu:o11

RUN mkdir -p /opt/odoo /opt/workspace
#UN wget -qO- https://nightly.odoo.com/11.0/nightly/src/odoo_11.0.latest.tar.gz | tar xz -C /opt/odoo/ --strip 1 

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" | tee -a /etc/apt/sources.list.d/pg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN apt-get update && sudo apt-get install postgresql-client-9.6 -y
#RUN echo "deb https://cli-assets.heroku.com/branches/stable/apt ./" | tee -a /etc/apt/sources.list && wget -O- https://cli-assets.heroku.com/apt/release.key | apt-key add -
#RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
#RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ libssl-dev apache2-utils git libxml2-dev sshfs tmux nodejs zip heroku python-watchdog phantomjs -y
#RUN npm install -g grunt-cli
RUN pip3 install pysftp uritools 
RUN pip3 install --upgrade pyOpenSSL
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN adduser -u 1000 --system --group --home /home/odoo --shell /bin/bash odoo
RUN chown odoo /opt/odoo -R
# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo/

ENV OPENERP_SERVER /etc/odoo/odoo.conf

VOLUME ["/opt/workspace"] 

#RUN cp /opt/odoo/setup/odoo /opt/odoo/odoo.py && chmod a+x /opt/odoo/odoo.py

RUN echo "odoo ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers

RUN ln -s /opt/odoo/odoo.py /bin/odoo && ln -s /opt/odoo/odoo.py /bin/odoo.py

EXPOSE 8069
USER odoo

#ENV RLOdoo=https://nightly.odoo.com/11.0/nightly/src/odoo_11.0.latest.tar.gz
ENV URLOdoo http://10.10.0.1/odoo_11.0.latest.tar.gz
#RUN wget -qO- https://nightly.odoo.com/11.0/nightly/src/odoo_11.0.latest.tar.gz | tar xz -C /opt/odoo/ --strip 1
RUN echo "$URLOdoo"
RUN wget -qO- "$URLOdoo" | tar xz -C /opt/odoo/ --strip 1
RUN cp /opt/odoo/setup/odoo /opt/odoo/odoo.py && chmod a+x /opt/odoo/odoo.py

COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo
ENV OPENERP_SERVER /etc/odoo/odoo.conf

ENTRYPOINT ["/entrypoint.sh"]
