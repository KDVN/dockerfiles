FROM kdvn/ubuntu

RUN mkdir -p /mnt/extra-addons /mnt/odoofilestore /opt/odoo /opt/pentaho_server

#RUN wget -qO- http://10.10.0.1/openerp_7.0.latest.tar.gz | tar xz -C /opt/oe7/ --owner=openerp --strip 1
RUN wget -qO- https://nightly.odoo.com/10.0/nightly/src/odoo_10.0.latest.tar.gz | tar xz -C /opt/odoo/ --strip 1

RUN adduser -u 1000 --system --group --home /home/odoo --shell /bin/bash odoo

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo/

ADD ./pentaho/java_server/ /opt/pentaho_server/
ADD ./pentaho/home/ /home/odoo

ENV OPENERP_SERVER /etc/odoo/odoo.conf

VOLUME ["/mnt/odoofilestore", "/mnt/extra-addons"] 

RUN cp /opt/odoo/setup/odoo /opt/odoo/odoo.py
RUN chmod a+x /opt/odoo/odoo.py

RUN chmod 775 /mnt/extra-addons/ /mnt/odoofilestore/ /home/odoo/ /opt/pentaho_server/ /opt/odoo/ -R
RUN chown -R 1000 /mnt/odoofilestore/ mnt/extra-addons /home/odoo/ /opt/pentaho_server/ /opt/odoo/

EXPOSE 8069

USER odoo
WORKDIR /opt/pentaho_server/

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/opt/odoo/odoo.py"]
