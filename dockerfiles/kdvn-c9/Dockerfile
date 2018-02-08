#COpy From https://github.com/kdelfour/supervisor-docker/blob/master/Dockerfile
# ------------------------------------------------------------------------------
# Based on a work at https://github.com/docker/docker.
# ------------------------------------------------------------------------------
# Pull base image.
FROM ubuntu
MAINTAINER Kevin Delfour <kevin@delfour.eu>
RUN sed -i 's/archive.ubuntu.com/mirrors.nhanhoa.com/g' /etc/apt/sources.list
# Install Supervisor.
RUN \
  apt-get update && \
  apt-get install -y supervisor && \
  rm -rf /var/lib/apt/lists/* && \
  sed -i 's/^\(\[supervisord\]\)$/\1\nnodaemon=true/' /etc/supervisor/supervisord.conf

# Define mountable directories.
VOLUME ["/etc/supervisor/conf.d"]

# ------------------------------------------------------------------------------
# Security changes
# - Determine runlevel and services at startup [BOOT-5180]
RUN update-rc.d supervisor defaults

# - Check the output of apt-cache policy manually to determine why output is empty [KRNL-5788]
RUN apt-get update | apt-get upgrade -y

# - Install a PAM module for password strength testing like pam_cracklib or pam_passwdqc [AUTH-9262]
RUN apt-get install libpam-cracklib build-essential g++ curl libssl-dev apache2-utils git libxml2-dev sshfs -y
RUN ln -s /lib/x86_64-linux-gnu/security/pam_cracklib.so /lib/security

# Define working directory.
#WORKDIR /etc/supervisor/conf.d
# ------------------------------------------------------------------------------
# Install Node.js
#RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -
#RUN curl -sL https://deb.nodesource.com/setup_6.x | bash 
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs wget sudo

RUN wget -qO- https://cli-assets.heroku.com/install-ubuntu.sh | sh
# ------------------------------------------------------------------------------
# Install Cloud9
RUN git clone https://github.com/c9/core.git /cloud9
WORKDIR /cloud9
RUN scripts/install-sdk.sh

# Tweak standlone.js conf
RUN sed -i -e 's_127.0.0.1_0.0.0.0_g' /cloud9/configs/standalone.js 

# Add supervisord conf
ADD conf/cloud9.conf /etc/supervisor/conf.d/

# ------------------------------------------------------------------------------
# Add volumes
RUN mkdir /workspace
VOLUME /workspace

# Install NPM
#RUN apt-get install npm -y
# ------------------------------------------------------------------------------
# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ------------------------------------------------------------------------------
# Expose ports.
EXPOSE 80
EXPOSE 3000

# ------------------------------------------------------------------------------
# Start supervisor, define default command.
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
