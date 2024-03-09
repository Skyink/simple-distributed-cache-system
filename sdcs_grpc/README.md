## SDCS based on grpc

基于grpc的简易分布式缓存系统

### 文件说明

1. `rpc_example`和`rpc_hello`目录下的代码为测试grpc原理使用的demo程序。
2. `sdcs_local_test`目录下的代码为不使用docker的本地测试项目程序。（在mac上运行）
3. `simple_dcs`目录下的代码为使用docker的最终项目程序。（在M1pro芯片的mac上运行，使用的是ARM架构相关的指令和依赖包）
4. `sdcs_final`目录下的代码为提交作业的最终项目程序。（老师验证代码使用x86架构的计算机，故调整为相关的指令和依赖包）
5. `sdcs-testsuit`目录下的代码为老师提供的验证项目可行性的脚本文件。
6. 当前目录下的`app.py`文件，仅用于测试web服务相关代码。
7. `grpc_request.paw`文件为接口调试工具Paw的测试文件。
