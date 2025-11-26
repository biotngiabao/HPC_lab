import grpc
import time
import subprocess

from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandResponse
import socket
import datetime
from constant import MetricType
from module.plugins.manager import PlugingManager
from module.plugins._base import BasePlugin
import logging

plugin_manager = PlugingManager()
plugin_manager.load_plugins()

last_metric = MetricType.CPU


def command_stream():
    current_metric = MetricType.CPU

    while True:
        plugin = plugin_manager.get_plugin(current_metric)

        value = "Metric not found"
        if plugin is not None:
            value = plugin.run()
            if value is None:
                value = "Cannot get metric value"
            else:
                value = str(value)

        yield CommandResponse(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hostname=socket.gethostname(),
            metric=current_metric,
            value=value,
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
