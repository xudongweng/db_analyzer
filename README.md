数据库后台服务：
功能 敏感信息审计

### 版本要求：

- python >=3.6.8
- Django 3.2.15
- apscheduler 3.9.1
- sqlalchemy 1.4.41
- numpy

## 系统环境

### 1.环境安装：

```shell
$ yum -y install python3 python3-devel
$ pip3 install PyMySQL==1.0.2
$ pip3 install django==3.2.15
$ pip3 install apscheduler==3.9.1
$ pip3 install sqlalchemy==1.4.41
$ pip3 install numpy
```

### 2.配置运行：

```shell
$ cd /usr/local && git clone https://github.com/xudongweng/db_analyzer.git
$ cd db-analyzer/src
$ python3 manage.py runserver 0.0.0.0:8000 --noreload
```

## docker环境

### 1.创建Dockerfile:

```shell
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
RUN cd /usr/local && git clone https://github.com/xudongweng/db_analyzer.git
WORKDIR /usr/local/db-analyzer/src
```

### 2.生成docker镜像

```shell
$ docker build -t django_env --target django_env .  
$ docker build -t db_analyzer_server --target db_analyzer_server .
```

### 3.配置运行docker

```shell
$ docker run -itd -p 0.0.0.0:8000:8000 --name da_server  db_analyzer_server  /bin/sh  
$ docker exec -it da_server python3 manage.py runserver 0.0.0.0:8000 --noreload
```
