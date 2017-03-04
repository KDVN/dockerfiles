FROM ubuntu

RUN sed -i 's/archive.ubuntu.com/ubuntutym.u-toyama.ac.jp/g' /etc/apt/sources.list && apt-get -y update && apt-get install -y software-properties-common
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y oracle-java8-installer

RUN apt-get dist-upgrade -y

RUN apt-get -y remove software-properties-common curl && apt-get autoremove -y && apt-get autoclean -y
RUN rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

VOLUME ["/opt/workspace", "/tmp"] 

# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle
WORKDIR /opt/workspace/extra-addons/jasper_reports/java
CMD ["./compile.sh"]
