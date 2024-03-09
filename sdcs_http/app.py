from flask import Flask
from flask import request
import json, requests, hashlib

app = Flask(__name__)

# 键值对存储缓存空间
cache_dict = {}
# 服务器节点地址
server_url = ["http://node1:5000", "http://node2:5000", "http://node3:5000"]
# 节点个数
server_cnt = 3
# 节点序号
# server_id = 0


# 写入/更新缓存请求
@app.route('/', methods=['POST'])
def update_cache():  # put application's code here
    request_data = request.json
    print("[update request] param: " + json.dumps(request_data))    # 打印请求参数

    # 构建存放空间
    dict_kv_list_to_update = []
    for i in range(0, server_cnt):
        dict_kv_list_to_update_index = {}
        dict_kv_list_to_update.append(dict_kv_list_to_update_index)

    # 遍历键值对，计算哈希值
    dict_kv_list = []
    index = 0
    for kv in request_data.items():
        dict_kv_list.append(kv)
    for i in range(len(dict_kv_list)):
        key = dict_kv_list[i][0]
        value = dict_kv_list[i][1]
        kv = {key: value}
        print(kv)
        # 计算哈希值
        md5 = hashlib.md5()                     # 创建MD5哈希对象
        md5.update(str(key).encode())           # 传入要计算哈希值的数据
        hash_code = md5.hexdigest()             # 计算出哈希值
        hash_value = 0
        for c in hash_code:
            hash_value = hash_value + ord(c)
        index = hash_value % server_cnt
        print(key + ": hashCode = " + hash_code + ", index = " + str(index))

        dict_kv_list_to_update[index][key] = value
        index = 0

    # 写入/更新至节点
    for index in range(0, server_cnt):
        if len(dict_kv_list_to_update[index]) == 0:
            break
        # 构建请求地址
        request_url = server_url[index] + "/save_to_cache"
        print("request to " + request_url)
        # 构建请求参数
        request_json = json.dumps(dict_kv_list_to_update[index])
        # 解析响应
        headers = {"Content-Type": "application/json", "Accept-Charset": "UTF-8"}
        response = requests.post(request_url, request_json, headers=headers)
        if response.status_code != 200:
            update_result = "server id = " + str(index) + " error!"
            print(update_result)
            return update_result, 400
        print("server id = " + str(index) + " response: \n" + response.text)

    return "update success!"


# 写入/更新至缓存
@app.route('/save_to_cache', methods=['POST'])
def save_to_cache():
    request_data = request.json
    print("[update to cache request] param: " + json.dumps(request_data))  # 打印请求参数

    dict_kv_list = []
    for kv in request_data.items():
        dict_kv_list.append(kv)
    for i in range(len(dict_kv_list)):
        key = dict_kv_list[i][0]
        value = dict_kv_list[i][1]
        kv = {key: value}
        cache_dict.update(kv)
    print(cache_dict)

    return "[update response] Total length = " + str(len(cache_dict))


# 读取缓存请求
@app.route('/<key>', methods=['GET'])
def get_cache(key):
    print("[get request] param: " + key)

    md5 = hashlib.md5()                     # 创建md5对象
    md5.update(str(key).encode())           # 传入要计算哈希值的数据
    hash_code = md5.hexdigest()
    # 累加hash_code各位的ASCII码值
    hash_value = 0
    for c in hash_code:
        hash_value = hash_value + ord(c)
    # 计算查询节点位置
    index = hash_value % server_cnt
    index = 0

    # 构建请求地址
    request_url = server_url[index] + "/search_from_cache"
    print("request to " + request_url)
    # 构建请求参数
    request_data = {"key": key}
    request_json = json.dumps(request_data)
    # 解析响应
    headers = {"Content-Type": "application/json", "Accept-Charset": "UTF-8"}
    response = requests.post(request_url, request_json, headers=headers)
    if response.status_code == 200:
        print("server id = " + str(index) + " response: \n" + response.text)
        response_dict = json.loads(response.text)
        if response_dict:
            return response_dict
        else:
            print("[get request] get None!")
            return "", 404
    else:
        print("search server id = " + str(index) + " error!")
        return "", 404


# 从缓存中读取
@app.route('/search_from_cache', methods=['POST'])
def search_from_cache():
    request_data = request.json
    print("[search from cache request] param: " + json.dumps(request_data))  # 打印请求参数

    key = request_data.get("key")
    # 查询本地缓存
    key_value = search_kv(key)
    if key_value:
        print("[get request] get k-v = " + key_value)
        return key_value
    else:
        return {}


# 查询本地缓存中的键值对
def search_kv(key):
    if key in cache_dict.keys():
        value = cache_dict.get(key)
        get_dict = {key: value}
        get_kv = json.dumps(get_dict)
        print("[search local key-value] get k-v = " + get_kv)
        return get_kv
    else:
        print("[search local key-value] get None!")
        return None


# 删除缓存请求
@app.route('/<key>', methods=['DELETE'])
def delete_cache(key):
    print("[delete request] param: " + key)

    md5 = hashlib.md5()  # 创建md5对象
    md5.update(str(key).encode())  # 传入要计算哈希值的数据
    hash_code = md5.hexdigest()
    # 累加hash_code各位的ASCII码值
    hash_value = 0
    for c in hash_code:
        hash_value = hash_value + ord(c)
    # 计算查询节点位置
    index = hash_value % server_cnt
    index = 0

    # 构建请求地址
    request_url = server_url[index] + "/delete_from_cache"
    print("request to " + request_url)
    # 构建请求参数
    request_data = {"key": key}
    request_json = json.dumps(request_data)
    # 解析响应
    headers = {"Content-Type": "application/json", "Accept-Charset": "UTF-8"}
    response = requests.post(request_url, request_json, headers=headers)
    if response.status_code == 200:
        print("server id = " + str(index) + " response: \n" + response.text)
        delete_cnt = response.text
        return delete_cnt
    else:
        print("delete server id = " + str(index) + " error!")
        return "", 404


@app.route('/delete_from_cache', methods=['POST'])
def delete_from_cache():
    request_data = request.json
    print("[delete from cache request] param: " + json.dumps(request_data))  # 打印请求参数

    key = request_data.get("key")
    delete_cnt = 0  # 删除计数器
    value = None
    if key in cache_dict.keys():
        value = cache_dict.pop(key)
        delete_cnt = delete_cnt + 1

    # 打印删除的键值对
    delete_dict = {key: value}
    delete_kv = json.dumps(delete_dict)
    print("[delete response] delete k-v: " + delete_kv + ", delete_cnt = " + str(delete_cnt))
    return str(delete_cnt)


if __name__ == '__main__':
    app.run()
    # docker中的启动设置
    # app.run(host='0.0.0.0', port=5000)
