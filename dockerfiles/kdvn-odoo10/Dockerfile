FROM kdvn/ubuntu

RUN mkdir -p /mnt/extra-addons /mnt/oefilestore /opt/oe7 /opt/pentaho_server

#RUN wget -qO- http://10.10.0.1/openerp_7.0.latest.tar.gz | tar xz -C /opt/oe7/ --owner=openerp --strip 1
RUN wget -qO- http://nightly.odoo.com/7.0/nightly/src/openerp_7.0.latest.tar.gz | tar xz -C /opt/oe7/ --strip 1

RUN adduser -u 1000 --system --group --home /home/openerp --shell /bin/bash openerp

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./openerp-server.conf /etc/openerp/

ADD ./pentaho/java_server/ /opt/pentaho_server/
ADD ./pentaho/home/ /home/openerp

ENV OPENERP_SERVER /etc/openerp/openerp-server.conf

VOLUME ["/mnt/oefilestore", "/mnt/extra-addons"] 

RUN chown -R openerp /mnt/extra-addons /mnt/oefilestore /home/openerp /home/openerp /opt/pentaho_server
EXPOSE 8069

USER openerp
WORKDIR /opt/pentaho_server/

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/opt/oe7/openerp-server"]
