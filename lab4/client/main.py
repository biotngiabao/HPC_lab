import grpc
import time


from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandResponse
import socket
import datetime
from constant import MetricType
from module.plugins.manager import PlugingManager
from module.grpc import GRPCClient


def main():
    grpc_client = GRPCClient(address="localhost:50051", plugin_manager=PlugingManager())
    grpc_client.run()


if __name__ == "__main__":
    main()
