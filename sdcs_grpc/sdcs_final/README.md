### 启动方法一：直接启动
直接在当前目录下运行指令，完成打包镜像+启动容器。
```shell
docker-compose up
```

### 启动方法二：分步启动
1. 在当前目录下执行指令打包镜像。
   ```shell
   docker build -t cache_node ./sdcs
   ```

2. 需要修改`docker-compose.yaml`文件中的`build`参数，将每个节点中的`build`参数替换为`images`。

   ```shell
   services:
     node0:
       image: "cache_node"
   #    build:
   #      context: ./sdcs
   #      dockerfile: Dockerfile
       ports:
         - "9527:5000"
       tty: true
   ```

3. 在当前目录下执行指令启动容器。
   ```shell
   docker-compose up
   ```

   
### 其他说明
- 当前sources.list中使用的镜像源为x86架构的镜像地址，如需使用arm架构的镜像地址需要到文件中修改。
- 分步打包镜像+启动容器时，需要修改docker-compose中的指令，指定镜像名称。
- 如果遇到权限问题，在指令前添加`sudo`。