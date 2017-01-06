FROM ubuntu:16.04
RUN sed -i 's/archive.ubuntu.com/ubuntutym.u-toyama.ac.jp/g' /etc/apt/sources.list && apt-get update && apt-get dist-upgrade -y && apt-get install postgresql-client -y
RUN apt-get autoremove -y && apt-get autoclean -y
RUN rm -rf /var/lib/apt/lists/*
