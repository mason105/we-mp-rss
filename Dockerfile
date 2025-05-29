# 定义镜像源环境变量
FROM docker.1ms.run/ubuntu:20.04 AS base 
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update
RUN apt install -y python3 
RUN apt install -y python3-pip

# 自动设置时区（如上海）
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN apt install -y --no-install-recommends firefox 


FROM base
# 安装系统依赖
WORKDIR /app

RUN export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# 复制Python依赖文件
# 复制后端代码
COPY . .
COPY requirements.txt .
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN rm -rf ./web_ui
RUN rm -rf ./venv

COPY ./config.example.yaml  ./config.yaml
RUN chmod +x ./start.sh
# 暴露端口
EXPOSE 8001

# 启动命令
# CMD ["uvicorn", "web:app", "--host", "0.0.0.0", "--port", "8001"]
# CMD ["python", "main.py"]
CMD ["./start.sh"]