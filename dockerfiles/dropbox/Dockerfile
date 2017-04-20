#COPY from https://hub.docker.com/r/mhimmer/dropbox/~/dockerfile/ 
# THIS ONE JUST FOR UPDATE ONLY
FROM ubuntu:latest
MAINTAINER Marcos Himmer <m@himmer.cl>

USER root

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -o Dpkg::Options::="--force-confnew" --force-yes -fuy dist-upgrade
RUN apt-get install -y wget python-software-properties
RUN rm /root/.dropbox-dist/dropbox-lnx* -rf
RUN cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf - 
RUN wget -O /usr/bin/dropbox.py "https://www.dropbox.com/download?dl=packages/dropbox.py"
RUN chmod +x /usr/bin/dropbox.py

# Cleanup
RUN apt-get remove --purge -y wget; apt-get -y autoremove; apt-get clean
RUN rm -rf /tmp/* /var/tmp/* /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN mkdir -p /root/Dropbox

WORKDIR /root

VOLUME ["/root/Dropbox", "/root/.dropbox"]

ENTRYPOINT ["/bin/bash","-c","/root/.dropbox-dist/dropboxd;/bin/bash"]
