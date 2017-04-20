FROM ubuntu
RUN mkdir /home/testing
RUN chown 999 /home/testing 
ONBUILD RUN chown $UID /home/testing
ONBUILD RUN mkdir -p /home/testing/helloworld

CMD ["bash"]
