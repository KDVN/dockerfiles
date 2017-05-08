FROM kdvn/ubuntu

RUN mkdir -p /opt/extra-addons /opt/odoo /opt/odoodata

#RUN wget -qO- http://10.10.0.1/openerp_7.0.latest.tar.gz | tar xz -C /opt/oe7/ --owner=openerp --strip 1
RUN wget -qO- https://nightly.odoo.com/10.0/nightly/src/odoo_10.0.latest.tar.gz | tar xz -C /opt/odoo/ --strip 1

RUN adduser -u 1000 --system --group --home /home/odoo --shell /bin/bash odoo

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo/

ENV OPENERP_SERVER /etc/odoo/odoo.conf

VOLUME ["/opt/workspace","/opt/odoodata","/opt/extra-addons"] 

RUN cp /opt/odoo/setup/odoo /opt/odoo/odoo.py && chmod a+x /opt/odoo/odoo.py

RUN chmod 775 /opt/extra-addons/ /opt/odoodata -R

RUN chown -R 1000 /opt/extra-addons /home/odoo/ /opt/odoodata

EXPOSE 8069

USER odoo

WORKDIR /opt/odoo

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/opt/odoo/odoo.py"]
