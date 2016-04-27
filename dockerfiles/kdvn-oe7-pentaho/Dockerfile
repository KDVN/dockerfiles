FROM kdvn/openerp7

USER root
RUN apt-get update -y && apt-get install ant-contrib -y
RUN mkdir -p /opt/pentaho_server

# Copy entrypoint script and Odoo configuration file
ADD ./java_server/ /opt/pentaho_server/
ADD ./home/ /root/


WORKDIR /opt/pentaho_server

CMD ["/bin/bash"]
