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
        "metrics": ["cpu"],
        "plugins": ["module.plugins.cpu.CpuPlugin"], # Sửa lại đúng đường dẫn plugin cpu của bạn
        "master_hostname": "LAPTOP-UMVK4LFU"
    }

DEFAULT_CONFIG = load_default_config()

class ConfigManager:
    def __init__(self, host='localhost', port=12379, key='/monitor/config'):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.key = key
        
        # 1. Dùng biến này lưu config, KHÔNG DÙNG LOCK phức tạp nữa
        # Trong Python, việc gán dict (self.config = new_dict) là atomic (an toàn thread cơ bản)
        self.config = DEFAULT_CONFIG.copy()
        
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
                        self.logger.info(f"Initial config loaded: {self.config}")
                    
                    # Bắt đầu watch (Hàm này sẽ block thread này, không ảnh hưởng Main Thread)
                    events, cancel = self.client.watch(self.key)
                    for event in events:
                        try:
                            new_val = event.value.decode('utf-8')
                            self.config = json.loads(new_val) # Cập nhật thẳng, không cần lock cầu kỳ
                            self.logger.info("Config updated dynamically!")
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.error(f"Watch error: {e}. Reconnecting in 5s...")
                    self.client = None # Reset để connect lại
            
            time.sleep(5) # Chờ 5s trước khi thử lại nếu mất kết nối

    def get_config(self):
        # Trả về trực tiếp, cực nhanh, không bao giờ bị block
        return self.config

    def is_master_node(self) -> bool:
        return self.hostname == self.config.get("master_hostname")

    def update_active_metrics(self, new_metrics):
        # Logic update metrics giữ nguyên, nhưng thêm check client
        if not self.client: return False
        if not self.is_master_node(): return False
        
        new_conf = self.config.copy()
        if set(new_conf.get("metrics", [])) == set(new_metrics):
            return True
            
        new_conf["metrics"] = new_metrics
        try:
            self.client.put(self.key, json.dumps(new_conf))
            return True
        except:
            return False