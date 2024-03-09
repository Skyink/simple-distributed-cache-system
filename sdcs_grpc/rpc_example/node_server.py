import json

import flask
import grpc
import example_pb2, example_pb2_grpc
import threading
from concurrent import futures
import time
import os

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

app = flask.Flask(__name__)

server_url = ["http://node1", "http://node2", "http://node3"]
server_cnt = 3
server_index = os.environ.get('SERVER_INDEX', 0)
print("Server " + str(server_index) + " is starting..")

cache = {}
total_cnt = 0


class Node(example_pb2_grpc.CacheNodeServicer):
    def UpdateKeyValue(self, request, context):
        global total_cnt
        update_cnt = 0
        kv_map = request.kv_map

        for key, value in kv_map.items():
            is_exist = cache.get(key)
            if is_exist is None:
                cache.update({key: value})
                update_cnt += 1
                total_cnt += 1

        print("Successfully updated k-v cnt = " + str(update_cnt))
        return example_pb2.UpdateKeyValueResponse(cnt=update_cnt)


# grpc服务器
def run_grpc_server():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    example_pb2_grpc.add_CacheNodeServicer_to_server(Node(), grpc_server)
    grpc_server.add_insecure_port("127.0.0.1:8001")
    grpc_server.start()
    print("server start...")

    try:
        while True:
            print("server is running..")
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        grpc_server.stop(0)


# grpc客户端
def grpc_update_client(map={}):
    conn = grpc.insecure_channel("127.0.0.1:8001")
    client = example_pb2_grpc.CacheNodeStub(channel=conn)
    request = example_pb2.UpdateKeyValueRequest(kv_map=map)
    rsp = client.UpdateKeyValue(request)
    print(rsp.result)
    return rsp.result


# 启动grpc服务器
grpc_thread = threading.Thread(target=run_grpc_server)
grpc_thread.start()


@app.route("/test", methods=["POST"])
def update_key_value():
    k1 = "k1"
    v1 = "v1"
    k2 = "k2"
    v2 = "v2"
    kv_map = {k1: v1}
    kv_map.update({k2: v2})
    return grpc_update_client(kv_map)


@app.route("/get", methods=["POST"])
def search_local():
    print(cache)
    reply = json.dumps(cache)
    return reply


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001)
