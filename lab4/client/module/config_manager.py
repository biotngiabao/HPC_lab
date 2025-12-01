import etcd3
import json
import threading
import logging
import os
import socket
# Cấu hình mặc định phòng khi mất kết nối
def load_default_config():
    config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading default config from config.json: {e}")
        # Fallback to hardcoded config if file missing or invalid
        return {
            "interval": 5,
            "metrics": ["cpu"],
            "plugins": ['module.plugins._cpu.CPUPlugin'],
            "master_hostname": "LAPTOP-UMVK4LFU"
        }
DEFAULT_CONFIG = load_default_config()

class ConfigManager:
    def __init__(self, host='localhost', port=12379, key='/monitor/config'):
        self.client = etcd3.client(host=host, port=port)
        self.key = key
        self.config = DEFAULT_CONFIG
        self.lock = threading.Lock()
        
        self.hostname = socket.gethostname() 
        logging.info(f"ConfigManager initialized on host: {self.hostname}")
        
        self._load_initial_config()
        
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
                self.client.put(self.key, json.dumps(DEFAULT_CONFIG))
        except Exception as e:
            logging.error(f"Error loading config: {e}")

    def _watch_changes(self):
        try:
            events_iterator, cancel = self.client.watch(self.key)
            for event in events_iterator:
                try:
                    raw_value = event.value.decode('utf-8')
                    logging.debug(f"Raw config value from etcd: {raw_value}")
                    try:
                        parsed_config = json.loads(raw_value)
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON in etcd config: {raw_value} | Error: {e}")
                        continue
                    
                    with self.lock:
                        self.config = parsed_config
                    logging.info(f"Config updated: {self.config}")
                    
                except Exception as e:
                    logging.error(f"Error parsing config update: {e}")
        except Exception as e:
             logging.error(f"Watch thread error (etcd connection lost?): {e}")

    def get_config(self):
        with self.lock:
            return self.config
    
    def is_master_node(self) -> bool:
        current_config = self.get_config()
        master_host = current_config.get("master_hostname")
        
        if not master_host:
            return False
            
        return self.hostname == master_host