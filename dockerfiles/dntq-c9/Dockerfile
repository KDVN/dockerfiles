FROM ubuntu

USER root

RUN mkdir -p /opt/c9sdk /opt/workspace
RUN apt-get update && apt-get install apt-transport-https wget sudo -y
RUN echo "deb https://cli-assets.heroku.com/branches/stable/apt ./" | tee -a /etc/apt/sources.list && wget -O- https://cli-assets.heroku.com/apt/release.key | sudo apt-key add -
RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ curl libssl-dev apache2-utils git libxml2-dev sshfs tmux sudo nodejs zip heroku -y
RUN apt-get install python -y
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy entrypoint script and Odoo configuration file
#COPY ./entrypoint.sh /
#COPY ./openerp-server.conf /etc/openerp/

#NV OPENERP_SERVER /etc/odoo/openerp-server.conf

VOLUME ["/opt/workspace"]
RUN useradd -m -G sudo dntq
RUN chown -R dntq /opt/c9sdk /opt/workspace
RUN usermod --shell /bin/bash --home /opt/c9sdk dntq

EXPOSE 8000
RUN echo "dntq ALL = NOPASSWD : /usr/bin/apt-get , /usr/bin/aptitude , /usr/sbin/usermod " | tee -a /etc/sudoers
USER dntq
RUN git clone git://github.com/c9/core.git /opt/c9sdk && cd /opt/c9sdk && scripts/install-sdk.sh

WORKDIR /opt/c9sdk
#RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' ~/configs/standalone.js 
COPY ./entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
