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
        # Biến lưu trạng thái danh sách plugin cũ để so sánh
        last_loaded_paths = []

        while True:
            # 1. Lấy cấu hình mới nhất
            config = self.config_manager.get_config()
            interval = config.get("interval", 5)
            metrics = config.get("metrics", ["cpu"])
            current_plugin_paths = config.get("plugins", [])

            # 2. [QUAN TRỌNG] Kiểm tra xem danh sách plugin có đổi không
            # Nếu đổi thì mới gọi PluginManager để load lại (tránh load thừa gây chậm)
            if current_plugin_paths != last_loaded_paths:
                self.logger.info(f"Plugin config changed. Reloading: {current_plugin_paths}")
                self.plugin_manager.load_plugins(current_plugin_paths)
                last_loaded_paths = current_plugin_paths

            # 3. Chạy vòng lặp thu thập dữ liệu
            for metric_name in metrics:
                self.logger.info(f"Processing metric: {metric_name}")
                
                # Tìm plugin tương ứng với metric (vd: "cpu")
                plugin = self.plugin_manager.get_plugin(metric_name)

                value = "Metric not found"
                unit = "N/A"
                
                if plugin:
                    try:
                        val = plugin.run()
                        if val is None:
                             value = "None"
                        else:
                             value = str(val)
                        
                        # Lấy unit an toàn hơn
                        unit = getattr(plugin, "unit", "N/A")
                    except Exception as e:
                        self.logger.error(f"Error running plugin {metric_name}: {e}")
                        value = "Error"

                yield CommandResponse(
                    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    hostname=socket.gethostname(),
                    metric=metric_name, 
                    value=value,
                    unit=unit,
                )

            time.sleep(interval)