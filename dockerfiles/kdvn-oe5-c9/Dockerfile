FROM kdvn/ubuntu

USER root
RUN adduser -u 1000 --system --group --home /home/openerp --shell /bin/bash openerp
RUN echo "openerp ALL = NOPASSWD : /usr/bin/tee , /bin/sed , /usr/bin/apt-get , /usr/bin/aptitude , /usr/sbin/usermod " | tee -a /etc/sudoers
RUN pip install cherrypy==3.1.2
RUN mkdir -p /mnt/extra-addons /mnt/oefilestore /opt/c9sdk /opt/workspace
RUN apt-get update && apt-get install apt-transport-https wget -y
RUN echo "deb https://cli-assets.heroku.com/branches/stable/apt ./" | tee -a /etc/apt/sources.list 
RUN wget -O- https://cli-assets.heroku.com/apt/release.key | apt-key add -
RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ curl libssl-dev apache2-utils git libxml2-dev sshfs tmux nodejs zip heroku -y
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" | tee -a /etc/apt/sources.list.d/pg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN apt-get update && sudo apt-get install apt-transport-https sudo curl postgresql-client python-formencode -y
RUN rm -rf /etc/sudoers && apt-get install sudo -f -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy entrypoint script and Odoo configuration file
#COPY ./entrypoint.sh /
#COPY ./openerp-server.conf /etc/openerp/

#NV OPENERP_SERVER /etc/odoo/openerp-server.conf

VOLUME ["/mnt/oefilestore", "/mnt/extra-addons", "/opt/workspace"] 

RUN chown -R openerp /mnt/extra-addons /mnt/oefilestore /opt/c9sdk /opt/workspace
RUN usermod --shell /bin/bash --home /opt/c9sdk openerp
RUN echo "openerp ALL = NOPASSWD : /usr/bin/apt-get , /usr/bin/aptitude , /usr/sbin/usermod " | tee -a /etc/sudoers

EXPOSE 8000
EXPOSE 8069
EXPOSE 8080

USER openerp
RUN git clone git://github.com/c9/core.git /opt/c9sdk && cd /opt/c9sdk && cd /opt/c9sdk && scripts/install-sdk.sh

WORKDIR /opt/c9sdk
#RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' ~/configs/standalone.js 
COPY ./entrypoint.sh /
COPY ./openerp-server.conf /etc/openerp/

ENTRYPOINT ["/entrypoint.sh"]
