import etcd3
import json
import threading
import logging
import os
import socket
import time

# --- Helper load default giữ nguyên ---
def load_default_config():
    config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    # Config cứng mặc định
    return {
        "interval": 5,
        "metrics": ["cpu", "memory", "diskio", "network"],
        "plugins": [
            "module.plugins._cpu.CPUPlugin",
            "module.plugins._ram.RAMPlugin",
            "module.plugins._diskio.DiskIOPlugin",
            "module.plugins._network.NetworkPlugin",
            "module.plugins._process_count.ProcessCountPlugin"
        ]
    }

DEFAULT_CONFIG = load_default_config()

class ConfigManager:
    def __init__(self, host=None, port=None, key='/monitor/config'):
        self.logger = logging.getLogger(__name__)
        # Allow overriding etcd host/port via environment variables (used in k8s)
        env_host = os.environ.get('ETCD_HOST')
        env_port = os.environ.get('ETCD_PORT')
        self.host = env_host if env_host else (host if host is not None else 'localhost')
        self.port = int(env_port) if env_port else (port if port is not None else 2379)
        self.key = key
        
        # 1. Dùng biến này lưu config, KHÔNG DÙNG LOCK phức tạp nữa
        # Trong Python, việc gán dict (self.config = new_dict) là atomic (an toàn thread cơ bản)
        self.config = DEFAULT_CONFIG.copy()
        
        # 2. Lưu available metrics từ etcd (để validate commands)
        self.available_metrics = self.config.get("metrics", [])
        
        self.hostname = socket.gethostname()
        self.client = None

        # 2. Không kết nối ngay tại đây để tránh treo lúc khởi động
        # Chuyển việc kết nối và watch sang một thread riêng biệt hoàn toàn
        self.running = True
        self.bg_thread = threading.Thread(target=self._background_worker, daemon=True)
        self.bg_thread.start()

    def _connect(self):
        try:
            return etcd3.client(host=self.host, port=self.port)
        except Exception as e:
            self.logger.error(f"Etcd connection failed: {e}")
            return None

    def _background_worker(self):
        """
        Thread này chịu trách nhiệm: 
        1. Kết nối etcd (thử lại nếu fail)
        2. Load config ban đầu
        3. Watch thay đổi
        """
        self.logger.info("Background config worker started...")
        
        # Thử kết nối liên tục cho đến khi được
        while self.running:
            if self.client is None:
                self.client = self._connect()
            
            if self.client:
                try:
                    # Load lần đầu
                    val, meta = self.client.get(self.key)
                    if val:
                        self.config = json.loads(val.decode('utf-8'))
                        self.available_metrics = self.config.get("metrics", [])
                        self.logger.info(f"Initial config loaded: {self.config}")
                    
                    # Bắt đầu watch (Hàm này sẽ block thread này, không ảnh hưởng Main Thread)
                    events, cancel = self.client.watch(self.key)
                    for event in events:
                        try:
                            new_val = event.value.decode('utf-8')
                            new_config = json.loads(new_val)
                            self.available_metrics = new_config.get("metrics", [])
                            self.logger.info(f"Available metrics updated from etcd: {self.available_metrics}")
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.error(f"Watch error: {e}. Reconnecting in 5s...")
                    self.client = None # Reset để connect lại
            
            time.sleep(5) # Chờ 5s trước khi thử lại nếu mất kết nối

    def get_config(self):
        # Trả về trực tiếp, cực nhanh, không bao giờ bị block
        return self.config

    def get_available_metrics(self):
        """Lấy danh sách metrics có sẵn từ etcd"""
        return self.available_metrics

    def update_local_metrics(self, new_metrics):
        """
        Cập nhật metrics cục bộ (không gửi lên etcd)
        Chỉ chấp nhận metrics là tập con của available_metrics
        """
        # Validate: new_metrics phải là tập con của available_metrics
        valid_metrics = [m for m in new_metrics if m in self.available_metrics]
        
        if not valid_metrics:
            self.logger.warning(f"No valid metrics in command: {new_metrics}")
            return False
        
        if set(valid_metrics) != set(new_metrics):
            invalid = set(new_metrics) - set(self.available_metrics)
            self.logger.warning(f"Some metrics are not available: {invalid}")
        
        # Cập nhật config nội bộ
        new_conf = self.config.copy()
        new_conf["metrics"] = valid_metrics
        self.config = new_conf
        
        self.logger.info(f"Local metrics updated to: {valid_metrics}")
        return True