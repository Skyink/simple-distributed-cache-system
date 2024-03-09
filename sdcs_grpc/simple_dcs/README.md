# Simple Distributed Cache System

---
### 基本原理
TODO: 待补充

### 操作步骤

1. 节点逻辑功能的代码实现
   1. 编写`sdcs.proto`文件，定义gRPC的消息传递对象和格式。
   2. 在Terminal中进入proto文件所在目录，执行指令生成`xxx_pb2.py`和`xxx_pb2_grpc.py`文件。
       ```shell
      python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. sdcs.proto
       ```
   3. 在`cache_node.py`文件中，编辑每个节点对应的处理逻辑
      - 定义grpc对象的具体方法实现
      ```python
      class Node:
         def method1(self, request, context):
            # method1 implement
         def method2(self, request, context):
            # method2 implement
         def method3(self, request, context):
            # method3 implement
      ```
      - 定义grpc服务端并指定监听的端口，以多线程模式启动该服务，使之在后台持续监听 
      ```python
      def run_grpc_server():
         # run_grpc_server implement
      ```
      - 定义grpc客户端（对应不同的rpc方法） 
      ```python
      def grpc_xxx_client():
         # grpc_xxx_client implement
      ```
      - 定义外部http请求的各功能接口，配置路由 
      ```python
      @app.route("/xxx")
      def xxx_api():
         # api implement
      ```
         - 写入/更新接口：
      ```python
      # 写入/更新缓存请求
      @app.route('/', methods=['POST'])
      def update_cache():
          # 解析请求参数
          # 构建存放列表，每个列表对应一个服务器节点
          # 遍历参数中的键值对
              # 计算key的哈希值，将其添加到对应节点的存放列表
          # 通过rpc请求，将存放列表分配到对应节点
              # 在各自节点内完成写入/更新操作
          # 解析rpc的响应，放回HTTP的响应
          return "update_response" 
      ```
         - 查询接口
      ```python
      # 查询缓存请求
      @app.route('/<key>', methods=['GET'])
      def get_cache(key):
          # 解析请求参数key
          # 计算key的哈希值，根据key获得对应的节点号
          # 通过rpc请求对应节点，在节点内完成查询操作
          # 解析rpc的响应，返回HTTP的响应
          return "get_response"
      ```
         - 删除接口
      ```python
      # 删除缓存请求
      @app.route('/<key>', methods=['DELETE'])
      def delete_cache(key):
          # 解析请求参数key
          # 计算key的哈希值，根据key获得对应的节点号
          # 通过rpc请求对应节点，在节点内完成删除操作
          # 解析rpc的响应，返回HTTP的响应
          return "delete_response"
      ```

      - 在http接口中调用grpc客户端方法，实现节点间的rpc通信

2. 打包部署docker
   1. 将项目依赖包导入`requirements.txt`文件。
   2. 编写`Dockerfile`文件打包项目的镜像（大致如下，可以考虑压缩镜像大小进行优化）。
      ```Dockerfile
      # 指定基础镜像
      FROM ubuntu:20.04
      # 指定工作目录
      WORKDIR /
   
      # 更换apt-get镜像源
   
      # 更新apt-get并安装Python和pip环境
      RUN apt-get update -y \
        && apt-get install -y python3.9 \
        && apt-get install -y python3-pip \
        # 清理临时文件
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
   
      # 更换pip镜像源
   
      # 安装项目依赖的包
      RUN pip3 install -r requirements.txt
   
      # 暴露端口给处于同一网络的容器，不暴露给宿主机
      EXPOSE 8000
   
      # 启动flask的指令
      CMD flask --app cache_node.py run --host=0.0.0.0 --port=5000
      ```
   3. 先测试手动打包镜像，及启动容器。
      *！！打包前确认一下系统架构，arm架构使用的镜像源，x86系统使用x86架构的镜像源！！*
      - 在Terminal中进入`Dockerfile`所在目录，执行`docker build`指令生成镜像。
         其中，`image_name`为自定义的镜像名称，
         `ENV_CONFIG`是需要设置的环境变量名称，
         `MY_CONFIG_VALUE`是自定义的环境变量的值。
      ```shell
      docker build -t image_name .
      ```
      - 使用`docker run`指令启动容器。 
      其中，`host_port`表示要指定的宿主机端口，
      `docker_name`表示要启动的容器的名称，
      `docker_port`表示容器中的端口，
      `image_name`是之前打包的镜像名称。
       ```shell
       docker run --name=docker_name -t -p host_port:docker_port image_name
       ```
   4. 使用`docker-compose.yaml`文件，在docker部署节点。
      执行以下指令运行`docker-compose.yaml`文件。
      ```shell
      docker-compose up
      ```
      通过`docker-compose`启动的容器之间可以相互解析容器名的DNS地址。
   
