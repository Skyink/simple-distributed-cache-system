import grpc

import hello_pb2
import hello_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.MsgServiceStub(channel)
        response = stub.GetMsg(hello_pb2.MsgRequest(name='world'))
    print("Client received: " + response.msg)


if __name__ == '__main__':
    run()