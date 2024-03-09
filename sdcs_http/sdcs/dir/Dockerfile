FROM ubuntu:20.04
WORKDIR /

COPY ./requirements.txt /requirements.txt

RUN sed -i s@/archive.ubuntu.com/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list \
    && apt-get update -y \
    && apt-get install -y python3-pip python3-dev \
    && pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

CMD flask --app app.py run --host=0.0.0.0 --port=5000
