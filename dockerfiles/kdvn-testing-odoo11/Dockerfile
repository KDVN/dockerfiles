FROM kdvn/ubuntu:o11

USER root
RUN apt-get update && apt-get install -y locales python-pip npm &&  localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8
RUN apt-get install -yq --no-install-suggests --no-install-recommends --force-yes expect-dev python-lxml libssl1.0.0 tcl git postgresql netcat
RUN wget -O /bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && chmod a+x /bin/wait-for-it
#UN easy_install -U coverage
RUN service postgresql restart && su -c "createuser -s root" postgres && su -c "createdb --encoding='utf8' -T template0 openerp_template" postgres
RUN git clone https://github.com/OCA/maintainer-quality-tools.git ${HOME}/maintainer-quality-tools
ENV PATH /root/maintainer-quality-tools/travis:$PATH
ENV TRAVIS_BUILD_DIR=/root/
ENV VERSION=11.0
ENV LINT_CHECK=1
ENV TRANSIFEX=1
ENV TESTS=1
ENV WKHTMLTOPDF_VERSION=0.12.4
RUN travis_install_nightly
RUN easy_install -U coverage
RUN apt-get remove -y npm python-pip curl && rm -rf /var/lib/apt/lists/* && apt-get -y autoremove && rm /*.tar*
ENTRYPOINT ["/bin/bash"]