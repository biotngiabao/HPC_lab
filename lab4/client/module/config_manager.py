import etcd3
import json
import threading
import logging
from constant import MetricType
# Cấu hình mặc định phòng khi mất kết nối
DEFAULT_CONFIG = {
    "interval": 5,
    "metrics": [MetricType.CPU, MetricType.MEMORY, MetricType.DISKIO, MetricType.NETWORK, MetricType.PROCESS_COUNT],
    "plugins": []
}

class ConfigManager:
    def __init__(self, host='localhost', port=12379, key='/monitor/config'):
        self.client = etcd3.client(host=host, port=port)
        self.key = key
        self.config = DEFAULT_CONFIG
        self.lock = threading.Lock()
        
        # Load config lần đầu
        self._load_initial_config()
        
        # Bắt đầu watch ở background
        watch_thread = threading.Thread(target=self._watch_changes, daemon=True)
        watch_thread.start()

    def _load_initial_config(self):
        try:
            value, meta = self.client.get(self.key)
            if value:
                self.config = json.loads(value.decode('utf-8'))
                logging.info(f"Loaded initial config: {self.config}")
            else:
                logging.warning("No config found in etcd, using default.")
                # Tự động đẩy config mặc định lên nếu chưa có
                self.client.put(self.key, json.dumps(DEFAULT_CONFIG))
        except Exception as e:
            logging.error(f"Error loading config: {e}")

    # ...existing code...
    def _watch_changes(self):
        events_iterator, cancel = self.client.watch(self.key)
        for event in events_iterator:
            try:
                raw_value = event.value.decode('utf-8')
                logging.debug(f"Raw config value from etcd: {raw_value}")  # Add this line
                try:
                    parsed_config = json.loads(raw_value)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in etcd config: {raw_value} | Error: {e}")
                    continue  # Skip update if JSON is invalid
                with self.lock:
                    self.config = parsed_config
                logging.info(f"Config updated: {self.config}")
                # self.plugin_manager.reload_plugins(self.config['plugins'])
            except Exception as e:
                logging.error(f"Error parsing config update: {e}")
    # ...existing code...

    def get_config(self):
        with self.lock:
            return self.config