import grpc
from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandRequest, CommandResponse
from constant import MetricType
import datetime
import socket
import time

from module.plugins.manager import PlugingManager
from module.plugins._base import BasePlugin
import logging


class GRPCClient:
    def __init__(self, address: str, plugin_manager: PlugingManager):
        self.channel = grpc.insecure_channel(address)
        self.stub = MonitorServiceStub(self.channel)
        self.last_command = MetricType.CPU

        self.plugin_manager = plugin_manager
        self.plugin_manager.load_plugins()

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"GRPCClient initialized with address: {address}")

    def run(self):
        responses = self.stub.CommandStream(self.command_stream())
        try:
            for response in responses:
                response: CommandRequest
                self.logger.info(f"Received command: {response.command}")

                self.last_command = response.command
        except grpc.RpcError as e:
            self.logger.error(f"RPC error: {e.code()} - {e.details()}")
        except Exception as e:
            self.logger.error(f"Error: {e}")

    def command_stream(self):
        current_metric = self.last_command

        while True:
            plugin = self.plugin_manager.get_plugin(current_metric)

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
                unit=plugin.unit if plugin else "N/A",
            )

            time.sleep(0.2)

            if current_metric != self.last_command:
                current_metric = self.last_command
