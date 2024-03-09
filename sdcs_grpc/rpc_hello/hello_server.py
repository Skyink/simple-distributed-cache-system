import grpc
import hello_pb2
import hello_pb2_grpc
from concurrent import futures
import time

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class MsgServicer(hello_pb2_grpc.MsgServiceServicer):
    def GetMsg(self, request, context):
        print("Received name: %s" % request.name)
        return hello_pb2.MsgResponse(msg='Hello, %s!' % request.name)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hello_pb2_grpc.add_MsgServiceServicer_to_server(MsgServicer(), server)
    server.add_insecure_port('0.0.0.0:50051')
    server.start()
    print("server start..")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
            print("server is running..")
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
