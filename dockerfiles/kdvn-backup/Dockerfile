FROM alpine

RUN apk update && apk upgrade && apk add tzdata rsync rdiff-backup postgresql-client openssh-client git heirloom-mailx ssmtp bash borgbackup tar
RUN cp /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime && echo "Asis/Ho_Chi_Minh" >  /etc/timezone
RUN apk del tzdata

ADD entrypoint.sh entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
