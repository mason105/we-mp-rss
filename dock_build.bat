echo off
chcp 65001
set name=we-mp-rss:latest
docker build -t %name% .
REM 获取所有运行中容器的ID并逐个停止
FOR /f "tokens=*" %%i IN ('docker ps -q') DO docker stop %%i
docker container prune -f
docker run -d --name we-mp-rss -p 8001:8001 -v C:\Users\Administrator\Desktop\Wx\we-mp-rss:/work we-mp-rss
docker exec -it we-mp-rss /bin/bash

if "%1"=="-p" (
docker image tag %name% ghcr.io/rachelos/%name%
docker image ls
docker push ghcr.io/rachelos/%name%
)