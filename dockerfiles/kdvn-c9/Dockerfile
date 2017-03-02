FROM kdvn/ubuntu

USER root

RUN mkdir -p /opt/c9sdk /opt/workspace
RUN apt-get update && apt-get install apt-transport-https -y
RUN echo "deb https://cli-assets.heroku.com/branches/stable/apt ./" | tee -a /etc/apt/sources.list && wget -O- https://cli-assets.heroku.com/apt/release.key | apt-key add -
RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install git build-essential g++ curl libssl-dev apache2-utils git libxml2-dev sshfs tmux sudo nodejs zip heroku -y

RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

VOLUME ["/opt/workspace"] 

RUN adduser -u 1000 --system --group --home /home/devuser --shell /bin/bash devuser
RUN chown -R devuser /opt/c9sdk /opt/workspace
RUN usermod --shell /bin/bash --home /opt/c9sdk devuser
RUN echo "devuser ALL = NOPASSWD : /usr/bin/apt-get , /usr/bin/aptitude , /usr/sbin/usermod " | tee -a /etc/sudoers

EXPOSE 3000

USER devuser
RUN git clone git://github.com/c9/core.git /opt/c9sdk && cd /opt/c9sdk && cd /opt/c9sdk && scripts/install-sdk.sh

WORKDIR /opt/c9sdk
#RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' ~/configs/standalone.js 
COPY ./entrypoint.sh /

COPY ./han7cpoe /bin/
COPY ./hcm7cpoe /bin/

ENV PATH "$PATH:/opt/oe7"

ENTRYPOINT ["/entrypoint.sh"]
