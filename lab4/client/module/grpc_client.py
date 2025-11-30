import grpc
from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandRequest, CommandResponse
# from constant import MetricType # Bỏ hoặc không dùng tới nữa vì dùng string từ etcd
import datetime
import socket
import time
import logging

class GRPCClient:
    
    def __init__(self, address: str, plugin_manager, config_manager):
        self.channel = grpc.insecure_channel(address)
        self.stub = MonitorServiceStub(self.channel)
        
        self.plugin_manager = plugin_manager
        self.config_manager = config_manager 
        self.plugin_manager.load_plugins()

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"GRPCClient initialized with address: {address}")

    def run(self):
        responses = self.stub.CommandStream(self.command_stream())
        try:
            for response in responses:
                self.logger.info(f"Server ACK: {response.commandList}")
        except Exception as e:
            self.logger.error(f"Error: {e}")

    def command_stream(self):
        while True:
            
            config = self.config_manager.get_config()
            interval = config.get("interval", 5)      
            metrics = config.get("metrics", ["cpu"])  

            
            for metric_name in metrics:
                self.logger.info(f"Processing metric: {metric_name}")
                
                plugin = self.plugin_manager.get_plugin(metric_name)

                value = "Metric not found"
                unit = "N/A"
                
                if plugin:
                    val = plugin.run()
                    value = str(val) if val is not None else "Error"
                    unit = getattr(plugin, "unit", "N/A")

                yield CommandResponse(
                    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    hostname=socket.gethostname(),
                    metric=metric_name, 
                    value=value,
                    unit=unit,
                )

            time.sleep(interval)