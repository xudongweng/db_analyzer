FROM python:3.11.0-alpine as django_env

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
RUN apk update
RUN apk add  git
RUN pip install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip3 install PyMySQL==1.0.2
RUN pip3 install django==3.2.15
RUN pip3 install apscheduler==3.9.1
RUN pip3 install sqlalchemy==1.4.41
RUN pip3 install pyyaml==6.0

FROM django_env as db_analyzer_server
RUN cd /usr/local && git clone http://username:password@127.0.0.1/dba/db-analyzer.git
WORKDIR /usr/local/db-analyzer/src