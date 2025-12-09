import grpc
from generated.monitor_pb2_grpc import MonitorServiceStub
from generated.monitor_pb2 import CommandRequest, CommandResponse

# from constant import MetricType # Bỏ hoặc không dùng tới nữa vì dùng string từ etcd
import datetime
import socket
import time
import logging

class GRPCClient:
    
    def __init__(self, address: str, plugin_manager, config_manager) -> None:
        self.channel = grpc.insecure_channel(address)
        self.stub = MonitorServiceStub(self.channel)

        self.plugin_manager = plugin_manager
        self.config_manager = config_manager 
        self.plugin_manager.load_plugins()

        self.recived_commands = []
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"GRPCClient initialized with address: {address}")

    def run(self):
        responses = self.stub.CommandStream(self.command_stream())
        try:
            for response in responses:
                response: CommandRequest
                command_list = list(response.commandList)
                self.logger.info(f"Received command from server: {command_list}")

                # Cập nhật metrics nội bộ nếu command khác với trước đó
                if command_list != self.recived_commands:
                    self.recived_commands = command_list
                    
                    # Lấy available metrics từ etcd để validate
                    available = self.config_manager.get_available_metrics()
                    self.logger.info(f"Available metrics from etcd: {available}")
                    
                    # Cập nhật local metrics (sẽ tự động validate)
                    success = self.config_manager.update_local_metrics(self.recived_commands)
                    if success:
                        self.logger.info(f"Local metrics updated to: {self.recived_commands}")
                    else:
                        self.logger.error("Failed to update local metrics.")
        except grpc.RpcError as e:
            self.logger.error(f"RPC error: {e.code()} - {e.details()}")
        except Exception as e:
            self.logger.error(f"Error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Đóng channel gRPC để giải phóng tài nguyên."""
        try:
            self.channel.close()
            self.logger.info("gRPC channel closed.")
        except Exception as e:
            self.logger.error(f"Error closing channel: {e}")

    def command_stream(self):
        """Vòng lặp chính điều phối luồng gửi dữ liệu."""
        last_loaded_paths = []

        while True:
            # 1. Lấy cấu hình snapshot
            config = self.config_manager.get_config()
            interval = config.get("interval", 5)
            metrics = config.get("metrics", [])
            plugin_paths = config.get("plugins", [])

            # 2. Xử lý reload plugin nếu config thay đổi
            last_loaded_paths = self._check_and_reload_plugins(plugin_paths, last_loaded_paths)

            # 3. Gửi dữ liệu (hoặc Heartbeat)
            if metrics:
                for metric_name in metrics:
                    yield self._collect_metric_data(metric_name)
            else:
                # Nếu không có metric nào, gửi tin nhắn rỗng để giữ kết nối Server
                yield self._create_heartbeat()

            # 4. Ngủ theo cấu hình
            time.sleep(interval)


    def _check_and_reload_plugins(self, current_paths, last_paths):
        if set(current_paths) != set(last_paths):
            self.logger.info(f"Plugin config changed. Reloading plugins...")
            self.plugin_manager.load_plugins(current_paths)
            return current_paths
        return last_paths

    def _collect_metric_data(self, metric_name):
        plugin = self.plugin_manager.get_plugin(metric_name)
        
        value = "Metric not found"
        unit = "N/A"

        if plugin:
            try:
                # Chạy logic thu thập (có thể tốn thời gian/CPU)
                raw_val = plugin.run()
                value = str(raw_val) if raw_val is not None else "None"
                unit = getattr(plugin, "unit", "N/A")
            except Exception as e:
                self.logger.error(f"Plugin error [{metric_name}]: {e}")
                value = "Error"

        return CommandResponse(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hostname=socket.gethostname(),
            metric=metric_name,
            value=value,
            unit=unit,
        )

    def _create_heartbeat(self):
        # self.logger.debug("Sending heartbeat...")
        return CommandResponse(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hostname=socket.gethostname(),
            metric="heartbeat",
            value="alive",
            unit=""
        )