import json

import flask
import grpc
import example_pb2, example_pb2_grpc
import threading
from flask import request
from concurrent import futures

app = flask.Flask(__name__)

cache = {}
total_cnt = 0


class Node(example_pb2_grpc.CacheNodeServicer):
    def UpdateKeyValue(self, request, context):
        global total_cnt
        update_cnt = 0
        kv_map = request.kv_map

        for key, value in kv_map.items():
            is_exist = cache[key]
            if is_exist is None:
                cache.update({key: value})
                update_cnt += 1
                total_cnt += 1

        return example_pb2.UpdateKeyValueResponse(cnt=update_cnt)


# grpc客户端
def grpc_update_client(map={}):
    conn = grpc.insecure_channel("node1:8001")
    client = example_pb2_grpc.CacheNodeStub(channel=conn)
    request = example_pb2.UpdateKeyValueRequest(kv_map=map)
    rsp = client.UpdateKeyValue(request)
    cntStr = str(rsp.cnt)
    print(cntStr)
    return cntStr


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
    app.run('0.0.0.0', port=5002)
