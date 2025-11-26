from generated.monitor_pb2_grpc import (
    MonitorServiceServicer,
    add_MonitorServiceServicer_to_server,
)
from generated.monitor_pb2 import CommandRequest, CommandResponse
import grpc
from concurrent import futures
from google.protobuf.json_format import MessageToJson


class MetricType:
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"


class MonitorService(MonitorServiceServicer):
    def CommandStream(self, request_iterator, context):
        command = MetricType.CPU
        try:
            for request in request_iterator:
                print(MessageToJson(request, indent=2))

                if request.metric == MetricType.CPU:
                    command = MetricType.MEMORY
                elif request.metric == MetricType.MEMORY:
                    command = MetricType.DISK
                elif request.metric == MetricType.DISK:
                    command = MetricType.CPU

                yield CommandRequest(command=command)

        except Exception as e:
            print(f"Error processing request stream: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise


def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_MonitorServiceServicer_to_server(MonitorService(), server)
    server.add_insecure_port("[::]:50051")

    print("Server started on port 50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    main()
