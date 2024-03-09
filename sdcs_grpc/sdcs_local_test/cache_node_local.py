import hashlib
import json
import os
import threading
import time
from concurrent import futures

import flask
import grpc
from flask import request
from google.protobuf import json_format

import sdcs_pb2
import sdcs_pb2_grpc


# 用于异步线程定时
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

app = flask.Flask(__name__)

# 静态配置节点信息
# server_url = ["http://node1", "http://node2", "http://node3"]
server_rpc_url = ["http://127.0.0.1:8000", "127.0.0.1:8001", "127.0.0.1:8002"]   # 本地测试
server_cnt = 1
server_index = os.environ.get('SERVER_INDEX', 1)            # 从环境变量中获取节点id
print("Server " + str(server_index) + " is starting..")

# 节点的本地缓存
cache = {}
# 节点中已存储的键值对总数
total_cnt = 0


class Node(sdcs_pb2_grpc.CacheNodeServicer):
    # rpc更新kv方法
    def UpdateKeyValue(self, request, context):
        global total_cnt
        update_cnt = 0
        # 入参
        kv_string = request.kv_string

        # 更新kv
        kv_map = json.loads(kv_string)
        for key, value in kv_map.items():
            is_exist = cache.get(key)
            if is_exist is None:
                # 校验本地无重复key值，则存储键值对
                cache.update({key: value})
                update_cnt += 1
                total_cnt += 1

        print("[grpc server{}] Successfully update k-v cnt = {} and total_cnt = {}".format(server_index, update_cnt, total_cnt))
        return sdcs_pb2.UpdateKeyValueResponse(update_cnt=update_cnt)

    # rpc查询kv方法
    def SearchKeyValue(self, request, context):
        # 入参
        key = request.key

        # 查询kv
        value = cache.get(key)
        resp_data = None
        if value:
            print("[grpc server{}] Successfully get k-v: {}".format(server_index, {key: value}))
            resp_data = json.dumps({key: value})
        else:
            print("[grpc server{}] Get none.. The key-value is not found!".format(server_index))
        return sdcs_pb2.SearchKeyValueResponse(kv_string=resp_data)

    # rpc删除kv方法
    def DeleteKeyValue(self, request, context):
        delete_cnt = 0
        # 入参
        key = request.key

        # 删除kv
        value = cache.pop(key, default=None)
        if value:
            delete_cnt += 1
            print("[grpc server{}] Successfully delete k-v: {}".format(server_index, {key: value}))
        else:
            print("[grpc server{}] Delete none.. The key-value is not found!".format(server_index))
        return sdcs_pb2.DeleteKeyValueResponse(delete_cnt=delete_cnt)


# grpc服务端
def run_grpc_server():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    sdcs_pb2_grpc.add_CacheNodeServicer_to_server(Node(), grpc_server)
    grpc_server.add_insecure_port(server_rpc_url[server_index])
    grpc_server.start()
    print("grpc_server of Node{} starts..".format(server_index))

    try:
        while True:
            print("grpc_server {} is running..".format(server_index))
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        grpc_server.stop(0)


# 启动grpc服务器
grpc_thread = threading.Thread(target=run_grpc_server)
grpc_thread.start()


# grpc客户端 更新请求
def grpc_update_client(kv_map={}, server_id=0):
    conn = grpc.insecure_channel(server_rpc_url[server_id])
    client = sdcs_pb2_grpc.CacheNodeStub(channel=conn)
    kv_string = json.dumps(kv_map)
    rpc_request = sdcs_pb2.UpdateKeyValueRequest(kv_string=kv_string)
    rsp = client.UpdateKeyValue(rpc_request)
    print("[grpc client{}] update response: {}".format(server_index, rsp))
    update_cnt = rsp.update_cnt
    return update_cnt


# grpc客户端 查询请求
def grpc_search_client(key=None, server_id=0):
    conn = grpc.insecure_channel(server_rpc_url[server_id])
    client = sdcs_pb2_grpc.CacheNodeStub(channel=conn)
    rpc_request = sdcs_pb2.SearchKeyValueRequest(key=key)
    rsp = client.SearchKeyValue(rpc_request)
    print("[grpc client{}] search response: {}".format(server_index, rsp))
    kv_string = rsp.kv_string
    return kv_string


# grpc客户端 删除请求
def grpc_delete_client(key=None, server_id=0):
    conn = grpc.insecure_channel(server_rpc_url[server_id])
    client = sdcs_pb2_grpc.CacheNodeStub(channel=conn)
    rpc_request = sdcs_pb2.DeleteKeyValueRequest(key=key)
    rsp = client.DeleteKeyValue(rpc_request)
    print("[grpc client{}] delete response: {}".format(server_index, rsp))
    delete_cnt = rsp.delete_cnt
    return delete_cnt


# 计算哈希值
def get_hash_value(key):
    # 计算哈希值
    md5 = hashlib.md5()  # 创建MD5哈希对象
    md5.update(str(key).encode())  # 传入要计算哈希值的数据
    hash_code = md5.hexdigest()  # 获得哈希值
    # 累加hash_code各位的ASCII码值
    hash_value = 0
    for c in hash_code:
        hash_value = hash_value + ord(c)
    return hash_value


# 写入/更新缓存请求
@app.route('/', methods=['POST'])
def update_cache():  # put application's code here
    request_data = request.json
    print("[node{} update request] param: {}".format(server_index, request_data))    # 打印请求参数≤

    # 构建存放空间
    kv_to_update_list = []
    for i in range(0, server_cnt):
        kv_list = {}
        kv_to_update_list.append(kv_list)

    # 遍历键值对，计算哈希值
    for key, value in request_data.items():
        index = 0                               # index重置
        print({key: value})
        # 计算哈希值
        hash_value = get_hash_value(key)
        # 计算对应的节点位置
        index = hash_value % server_cnt
        print("[node{} update request] param_key {} : index = {}".format(server_index, key, index))
        kv_to_update_list[index].update({key: value})

    # 写入/更新至节点
    result_cnt = 0
    for i in range(0, server_cnt):
        if len(kv_to_update_list[i]) == 0:
            break
        # 发送rpc请求
        result = grpc_update_client(kv_to_update_list[i], i)
        print("[node{} update rpc-request] grpc result: {}".format(server_index, result))
        # 解析rpc响应
        result_cnt += result
    print("[node{} update request] update {} key-value successfully!".format(server_index, result_cnt))

    return "update successfully! "


# 读取缓存请求
@app.route('/<key>', methods=['GET'])
def get_cache(key):
    print("[node{} search request] param: {}".format(server_index, key))

    # 计算哈希值
    hash_value = get_hash_value(key)
    # 计算对应的节点位置
    index = hash_value % server_cnt

    # 发送rpc请求
    result = grpc_search_client(key, index)
    print("[node{} search rpc-request] grpc result: {}".format(server_index, result))
    # 解析rpc响应
    kv = json.loads(result)
    value = kv.get(key)
    if value is None:
        print("[node{} search request] Target key not found!".format(server_index))
        return "Target key not found!", 404
    else:
        print("[node{} search request] Target key-value: {}".format(server_index, result))
        return result


# 删除缓存请求
@app.route('/<key>', methods=['DELETE'])
def delete_cache(key):
    print("[node{} delete request] param: {}".format(server_index, key))

    # 计算哈希值
    hash_value = get_hash_value(key)
    # 计算对应的节点位置
    index = hash_value % server_cnt

    # 发送rpc请求
    result = grpc_delete_client(key, index)
    print("[node{} delete rpc-request] grpc result: {}".format(server_index, result))
    # 解析rpc响应
    delete_cnt = 0
    delete_cnt += result
    print("[node{} delete request] delete {} key-value successfully!".format(server_index, delete_cnt))
    return delete_cnt


@app.route("/test", methods=["POST"])
def get_local_cache():
    print(cache)
    return json.dumps(cache)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
