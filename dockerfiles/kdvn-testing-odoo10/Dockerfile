FROM kdvn/ubuntu

USER root
RUN apt-get update && apt-get install -y locales &&  localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8
RUN apt-get install -yq --no-install-suggests --no-install-recommends --force-yes expect-dev python-lxml libssl1.0.0 tcl git postgresql
#UN easy_install -U coverage
RUN service postgresql restart && su -c "createuser -s root" postgres && su -c "createdb --encoding='utf8' -T template0 openerp_template" postgres
RUN git clone https://github.com/OCA/maintainer-quality-tools.git ${HOME}/maintainer-quality-tools
ENV PATH /root/maintainer-quality-tools/travis:$PATH
ENV TRAVIS_BUILD_DIR=/root/
ENV VERSION=10.0
ENV LINT_CHECK=1
ENV TRANSIFEX=1
ENV TESTS=1
RUN travis_install_nightly
RUN easy_install -U coverage
RUN apt-get remove -y python-pip curl && rm -rf /var/lib/apt/lists/* && apt-get remove npm -y && apt-get -y autoremove && rm /*odoo*.tar*
ENTRYPOINT ["/bin/bash"]
