FROM kdvn/odoo8

USER root

RUN mkdir -p /opt/extra-addons /opt/odoodata /opt/c9sdk /opt/workspace
RUN apt-get update && apt-get install apt-transport-https -y
RUN echo "deb https://cli-assets.heroku.com/branches/stable/apt ./" | tee -a /etc/apt/sources.list && wget -O- https://cli-assets.heroku.com/apt/release.key | apt-key add -
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ curl libssl-dev apache2-utils git libxml2-dev sshfs tmux sudo nodejs zip heroku -y
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy entrypoint script and Odoo configuration file
#COPY ./entrypoint.sh /
#COPY ./openerp-server.conf /etc/openerp/

#NV OPENERP_SERVER /etc/odoo/openerp-server.conf

VOLUME ["/opt/odoodata", "/opt/workspace"] 

RUN chown -R odoo /opt/workspace /opt/odoodata /opt/extra-addons /opt/c9sdk
RUN usermod --shell /bin/bash --home /opt/c9sdk odoo
#RUN echo "odoo ALL = NOPASSWD : /usr/bin/apt-get , /usr/bin/aptitude , /usr/sbin/usermod " | tee -a /etc/sudoers
RUN echo "odoo ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers
RUN ln -s /opt/odoo/odoo.py /bin/odoo
EXPOSE 8000
EXPOSE 8069

USER odoo
RUN git clone git://github.com/c9/core.git /opt/c9sdk && cd /opt/c9sdk && scripts/install-sdk.sh

WORKDIR /opt/c9sdk
#RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' ~/configs/standalone.js 
COPY ./entrypoint.sh /
ENV OPENERP_SERVER /etc/odoo/odoo.conf

ENTRYPOINT ["/entrypoint.sh"]
