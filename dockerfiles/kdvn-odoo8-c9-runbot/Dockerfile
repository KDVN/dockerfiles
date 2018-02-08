FROM kdvn/odoo8-runbot

USER root

RUN mkdir -p /opt/extra-addons /opt/odoodata /opt/c9sdk /opt/workspace
RUN apt-get update && apt-get install apt-transport-https sudo curl -y
RUN echo "deb https://cli-assets.heroku.com/branches/stable/apt ./" | tee -a /etc/apt/sources.list && wget -O- https://cli-assets.heroku.com/apt/release.key | apt-key add -
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ libssl-dev apache2-utils git libxml2-dev sshfs tmux nodejs zip heroku -y
RUN npm install -g grunt-cli && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

VOLUME ["/opt/odoodata", "/opt/workspace"] 

RUN chown -R odoo /opt/workspace /opt/odoodata /opt/extra-addons /opt/c9sdk &&  usermod --shell /bin/bash --home /opt/c9sdk odoo
RUN echo "odoo ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers

COPY ./odoo.bash /bin/odoo
RUN chmod a+x /bin/odoo

EXPOSE 8000
EXPOSE 8069

USER odoo
RUN git clone git://github.com/c9/core.git /opt/c9sdk && cd /opt/c9sdk && scripts/install-sdk.sh

WORKDIR /opt/c9sdk
#RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' ~/configs/standalone.js 
COPY ./entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
