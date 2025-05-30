echo off
chcp 65001
docker build -t we-mp-rss:latest .
REM 获取所有运行中容器的ID并逐个停止
FOR /f "tokens=*" %%i IN ('docker ps -q') DO docker stop %%i
docker container prune -f



docker run -d --name we-mp-rss -p 8001:8001 -v C:\Users\Administrator\Desktop\Wx\we-mp-rss:/work we-mp-rss
docker exec -it we-mp-rss /bin/bash