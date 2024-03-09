import json

from flask import Flask, request

app = Flask(__name__)

cache = dict()
update_cnt = 0
total_cnt = 0

# kv_string = "{\"key-16\": \"value 16\"}"
# kv_map = json.loads(kv_string)
# for key, value in kv_map.items():
#     is_exist = cache.get(key)
#     if is_exist is None:
#         # 校验本地无重复key值，则存储键值对
#         cache.update({key: value})
#         update_cnt += 1
#         total_cnt += 1
#         print("update!")
#     else:
#         print("fail")
# print(f"update cnt = {update_cnt}, total cnt = {total_cnt}")


kv_to_update_list = []
for server_i in range(0, 3):
    kv_list = {}
    kv_to_update_list.append(kv_list)

kv_to_update_list[0].update({"key1": "value1"})
kv_to_update_list[0].update({"key4": "value4"})
kv_to_update_list[1].update({"key2": "value2"})
kv_to_update_list[2].update({"key3": "value3"})

print(kv_to_update_list[0])
print(kv_to_update_list[1])
print(kv_to_update_list[2])




@app.route('/hello')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route("/", methods=['POST'])
def print_request():
    # 解析请求参数
    request_data = request.json
    data = request.data
    print("request param: {}".format(request_data))
    print(data)
    return request_data


if __name__ == '__main__':
    app.run()
