FROM kdvn/odoo

USER root

RUN mkdir -p /opt/extra-addons /opt/odoodata /opt/c9sdk /opt/workspace

RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ curl libssl-dev apache2-utils git libxml2-dev sshfs sudo nodejs -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy entrypoint script and Odoo configuration file
#COPY ./entrypoint.sh /
#COPY ./openerp-server.conf /etc/openerp/

#NV OPENERP_SERVER /etc/odoo/openerp-server.conf

VOLUME ["/opt/odoodata", "/opt/extra-addons", "/opt/workspace"] 

RUN chown -R odoo /opt/workspace /opt/odoodata /opt/extra-addons /opt/c9sdk
RUN usermod --shell /bin/bash --home /opt/c9sdk odoo
RUN echo "odoo ALL = NOPASSWD : /usr/bin/apt-get , /usr/bin/aptitude , /usr/sbin/usermod " | tee -a /etc/sudoers
RUN ln -s /opt/odoo/odoo.py /bin/odoo
EXPOSE 8000
EXPOSE 8069

USER odoo
RUN git clone git://github.com/c9/core.git /opt/c9sdk && cd /opt/c9sdk && scripts/install-sdk.sh

WORKDIR /opt/c9sdk
#RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' ~/configs/standalone.js 
COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo/
ENV OPENERP_SERVER /etc/odoo/odoo.conf

ENTRYPOINT ["/entrypoint.sh"]
