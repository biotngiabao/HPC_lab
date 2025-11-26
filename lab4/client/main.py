import grpc
import time
import subprocess

from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandResponse
import socket
import datetime
from command import get_metric_value, MetricType

last_metric = MetricType.CPU


def command_stream():
    current_metric = MetricType.CPU

    while True:
        yield CommandResponse(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hostname=socket.gethostname(),
            metric=current_metric,
            value=str(get_metric_value(current_metric)),
        )

        time.sleep(1)

        if current_metric != last_metric:
            current_metric = last_metric


def main():
    channel = grpc.insecure_channel("localhost:50051")
    stub = MonitorServiceStub(channel)

    responses = stub.CommandStream(command_stream())
    try:
        for response in responses:
            print(f"Received command: {response.command}")
            global last_metric
            last_metric = response.command
    except grpc.RpcError as e:
        print(f"RPC error: {e.code()} - {e.details()}")


if __name__ == "__main__":
    main()
