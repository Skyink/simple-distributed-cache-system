import hashlib
import json
import threading
import time
from concurrent import futures

import flask
import grpc
from flask import request

import sdcs_pb2
import sdcs_pb2_grpc


# 用于异步线程定时
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

app = flask.Flask(__name__)

# 静态配置节点信息
server_rpc_url = ["node0:8000", "node1:8000", "node2:8000"]
server_cnt = 3

# 节点的本地缓存
cache = dict()
# 节点中已存储的键值对总数
total_cnt = 0


class Node(sdcs_pb2_grpc.CacheNodeServicer):
    # rpc更新kv方法
    def UpdateKeyValue(self, request, context):
        global total_cnt
        update_cnt = 0
        # 入参
        kv_string = request.kv_string
        print("[grpc server] update_request param: {}".format(kv_string))

        # 更新kv
        kv_map = json.loads(kv_string)
        for key, value in kv_map.items():
            # 校验本地无重复key值，则total_cnt+1
            is_exist = cache.get(key)
            if is_exist is None:
                total_cnt += 1
            # 更新键值对
            cache.update({key: value})
            update_cnt += 1

        print("[grpc server] Successfully update k-v cnt = {} and total_cnt = {}".format(update_cnt, total_cnt))
        return sdcs_pb2.UpdateKeyValueResponse(update_cnt=update_cnt)

    # rpc查询kv方法
    def SearchKeyValue(self, request, context):
        # 入参
        key = request.key
        print("[grpc server] search_request param: {}".format(key))

        # 查询kv
        value = cache.get(key)
        resp_data = json.dumps({key: value})
        if value:
            print("[grpc server] Successfully get k-v: {}".format({key: value}))
        else:
            print("[grpc server] Get none.. The key-value is not found!")
        return sdcs_pb2.SearchKeyValueResponse(kv_string=resp_data)

    # rpc删除kv方法
    def DeleteKeyValue(self, request, context):
        delete_cnt = 0
        # 入参
        key = request.key
        print("[grpc server] delete_request param: {}".format(key))

        # 删除kv
        value = cache.pop(key, None)
        if value:
            delete_cnt += 1
            print("[grpc server] Successfully delete k-v: {}".format({key: value}))
        else:
            print("[grpc server] Delete none.. The key-value is not found!")
        return sdcs_pb2.DeleteKeyValueResponse(delete_cnt=delete_cnt)


# grpc服务端
def run_grpc_server():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    sdcs_pb2_grpc.add_CacheNodeServicer_to_server(Node(), grpc_server)
    grpc_server.add_insecure_port("0.0.0.0:8000")
    grpc_server.start()
    print("grpc_server starts..")

    try:
        while True:
            print("grpc_server is running..")
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
    print("[grpc client] update response: {}".format(rsp))
    update_cnt = rsp.update_cnt
    return update_cnt


# grpc客户端 查询请求
def grpc_search_client(key=None, server_id=0):
    conn = grpc.insecure_channel(server_rpc_url[server_id])
    client = sdcs_pb2_grpc.CacheNodeStub(channel=conn)
    rpc_request = sdcs_pb2.SearchKeyValueRequest(key=key)
    rsp = client.SearchKeyValue(rpc_request)
    print("[grpc client] search response: {}".format(rsp))
    kv_string = rsp.kv_string
    return kv_string


# grpc客户端 删除请求
def grpc_delete_client(key=None, server_id=0):
    conn = grpc.insecure_channel(server_rpc_url[server_id])
    client = sdcs_pb2_grpc.CacheNodeStub(channel=conn)
    rpc_request = sdcs_pb2.DeleteKeyValueRequest(key=key)
    rsp = client.DeleteKeyValue(rpc_request)
    print("[grpc client] delete response: {}".format(rsp))
    delete_cnt = rsp.delete_cnt
    return delete_cnt


# 计算哈希值
def get_hash_value(key):
    # 计算哈希值
    md5 = hashlib.md5()                 # 创建MD5哈希对象
    md5.update(str(key).encode())       # 传入要计算哈希值的数据
    hash_code = md5.hexdigest()         # 获得哈希值
    # 累加hash_code各位的ASCII码值
    hash_value = 0
    for c in hash_code:
        hash_value = hash_value + ord(c)
    return hash_value


# 写入/更新缓存请求
@app.route('/', methods=['POST'])
def update_cache():
    # 解析请求参数
    request_data = request.json
    print("[update request] param: {}".format(request_data))

    # 构建存放列表，每个列表对应一个服务器节点
    kv_to_update_list = []
    for server_i in range(0, server_cnt):
        kv_list = dict()
        kv_to_update_list.append(kv_list)

    # 遍历键值对，计算key的哈希值
    for key, value in request_data.items():
        print({key: value})
        # 计算哈希值
        hash_value = get_hash_value(key)
        # 计算分配的节点位置
        index = hash_value % server_cnt
        print("[update request] param_key {} : index = {}".format(key, index))
        # 将键值对添加到对应服务器节点的列表中
        kv_to_update_list[index].update({key: value})

    # 写入/更新至节点
    result_cnt = 0          # 累计写入/更新的键值对个数
    for server_i in range(0, server_cnt):
        if len(kv_to_update_list[server_i]) == 0:
            print("server list{} is none, skip!".format(server_i))
            continue
        # 发送rpc请求
        print("server list{} send grpc requset..".format(server_i))
        result = grpc_update_client(kv_to_update_list[server_i], server_i)
        print("[update rpc-request] grpc result: {}".format(result))
        # 解析rpc响应
        result_cnt += result
    print("[update request] update {} key-value successfully!".format(result_cnt))

    return "update successfully!"


# 读取缓存请求
@app.route('/<key>', methods=['GET'])
def get_cache(key):
    # 解析请求参数
    print("[search request] param: {}".format(key))

    # 计算哈希值
    hash_value = get_hash_value(key)
    # 计算分配的节点位置
    index = hash_value % server_cnt

    # 发送rpc请求
    result = grpc_search_client(key, index)
    print("[search rpc-request] grpc result: {}".format(result))
    # 解析rpc响应
    kv = json.loads(result)

    # 返回HTTP响应
    value = kv.get(key)
    if value is None:
        print("[search request] Target key not found!")
        return "", 404
    else:
        print("[search request] Target key-value: {}".format(kv))
        return result


# 删除缓存请求
@app.route('/<key>', methods=['DELETE'])
def delete_cache(key):
    # 解析请求参数
    print("[delete request] param: {}".format(key))

    # 计算哈希值
    hash_value = get_hash_value(key)
    # 计算分配的节点位置
    index = hash_value % server_cnt

    # 发送rpc请求
    result = grpc_delete_client(key, index)
    print("[delete rpc-request] grpc result: {}".format(result))
    # 解析rpc响应
    delete_cnt = 0
    delete_cnt += result

    # 返回HTTP响应
    print("[delete request] delete {} key-value successfully!".format(delete_cnt))
    return str(delete_cnt)


# 查询当前节点缓存中全部的键值对
@app.route("/getAll", methods=["POST"])
def get_local_cache():
    print(cache)
    return json.dumps(cache)


# 查询当前节点缓存中全部的键值对
@app.route("/checkHashCode/<key>", methods=["POST"])
def check_hash_code(key):
    print("[check hash key] param: {}".format(key))
    # 计算哈希值
    md5 = hashlib.md5()  # 创建MD5哈希对象
    md5.update(str(key).encode())  # 传入要计算哈希值的数据
    hash_code = md5.hexdigest()  # 获得哈希值
    # 累加hash_code各位的ASCII码值
    hash_value = 0
    for c in hash_code:
        hash_value = hash_value + ord(c)

    result = "{}-{}-{}".format(key, hash_code, hash_value)
    return result


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
