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
RUN chmod +x /usr/bin/dropbox.py && ln /usr/bin/dropbox.py /usr/bin/dropbox

# Cleanup
RUN apt-get -y autoremove; apt-get clean
RUN rm -rf /tmp/* /var/tmp/* /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN mkdir -p /root/Dropbox
RUN sysctl fs.inotify.max_user_watches=1048576
WORKDIR /root
COPY ./update.sh /

VOLUME ["/root/Dropbox", "/root/.dropbox"]

ENTRYPOINT ["/bin/bash","-c","/update.sh;/bin/bash"]
