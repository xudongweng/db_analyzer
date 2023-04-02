#!/bin/sh
docker build -t django_env --target django_env .
docker build -t db_analyzer_server --target db_analyzer_server .
docker run -itd -p 0.0.0.0:8000:8000 --name da_server  db_analyzer_server  /bin/sh
docker exec -it da_server python3 manage.py runserver 0.0.0.0:8000 --noreload
