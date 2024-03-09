FROM ubuntu:20.04
WORKDIR /

# 更换apt-get镜像源
COPY ./sources.list /etc/apt/
# 拷贝 requirements.txt
COPY ./requirements.txt .

# 更新apt-get并安装Python和pip环境
RUN apt-get update -y \
    && apt-get install -y python3.9 \
    && apt-get install -y python3-pip \
    # 清理临时文件
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # 更换pip镜像源
    && mkdir ~/.pip && \
    echo '[global]' > ~/.pip/pip.conf && \
    echo 'index-url = https://pypi.tuna.tsinghua.edu.cn/simple/' >> ~/.pip/pip.conf \
    # 安装项目依赖的包
    && pip3 install --upgrade setuptools \
    && pip3 install -r requirements.txt

# 拷贝主文件
COPY . .

# 暴露端口给处于同一网络的容器，不暴露给宿主机
EXPOSE 8000

CMD flask --app ./cache_node/cache_node.py run --host=0.0.0.0 --port=5000