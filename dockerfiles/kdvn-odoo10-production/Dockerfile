FROM kdvn/ubuntu

RUN mkdir -p /opt/extra-addons /opt/odoo /opt/odoodata /opt/custom-addons

RUN wget -qO- https://nightly.odoo.com/10.0/nightly/src/odoo_10.0.latest.tar.gz | tar xz -C /opt/odoo/ --strip 1 

RUN adduser -u 1000 --system --group --home /home/odoo --shell /bin/bash odoo

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
COPY ./odoo.conf /etc/odoo/

ENV OPENERP_SERVER /etc/odoo/odoo.conf

RUN mkdir /opt/logs

VOLUME ["/opt/custom-addons","/opt/odoodata","/opt/extra-addons","/opt/logs"] 

RUN cp /opt/odoo/setup/odoo /opt/odoo/odoo.py && chmod a+x /opt/odoo/odoo.py

RUN chmod 775 /opt/extra-addons/ /opt/odoodata /opt/custom-addons /opt/logs -R

RUN chown -R 1000 /opt/extra-addons /home/odoo/ /opt/odoodata /opt/logs
RUN echo "odoo ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" | tee -a /etc/apt/sources.list.d/pg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN apt-get update && sudo apt-get install postgresql-client-9.6 sudo  -y
RUN pip install pysftp && python -m easy_install --upgrade pyOpenSSL

EXPOSE 8069

USER odoo

WORKDIR /opt/odoo

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/opt/odoo/odoo.py"]
