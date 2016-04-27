FROM kdvn/ubuntu

RUN mkdir -p /mnt/extra-addons /mnt/oefilestore /opt/oe7 
RUN adduser -u 1000 --system --group --home /opt/oe7 --shell /bin/bash openerp && chown -R openerp /mnt/extra-addons /mnt/oefilestore

RUN wget -qO- http://10.10.0.1/openerp_7.0.latest.tar.gz | tar xz -C /opt/oe7/ --owner=openerp --strip 1
#ERUN wget -qO- http://nightly.odoo.com/7.0/nightly/src/openerp_7.0.latest.tar.gz | tar xz -C /opt/oe7/ --owner=openerp --strip 1

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./openerp-server.conf /etc/openerp/

RUN chown -R openerp:openerp /etc/openerp/openerp-server.conf /entrypoint.sh

ENV OPENERP_SERVER /etc/openerp/openerp-server.conf

VOLUME ["/mnt/oefilestore", "/mnt/extra-addons"] 

EXPOSE 8069

USER openerp

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/opt/oe7/openerp-server"]
