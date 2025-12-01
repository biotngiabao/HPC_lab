import json
import logging
import etcd3
from typing import List, Optional

class CommandSyncService:
    ETCD_KEY = "/monitor/command_list"

    def __init__(self, etcd_host='localhost', etcd_port=2379, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.etcd_host = etcd_host
        self.etcd_port = etcd_port
        self.client = self._connect()

    def _connect(self):
        try:
            return etcd3.client(host=self.etcd_host, port=self.etcd_port)
        except Exception as e:
            self.logger.error(f"Failed to connect to etcd at {self.etcd_host}:{self.etcd_port}: {e}")
            return None

    def set_commands(self, command_list: List[str]) -> bool:
        if not self.client:
            self.logger.error("Etcd client is not connected. Cannot set commands.")
            return False

        try:
            payload = json.dumps(command_list)
            self.client.put(self.ETCD_KEY, payload)
            self.logger.info(f"Successfully pushed commands to etcd: {payload}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write commands to etcd: {e}")
            return False

    def get_commands(self) -> List[str]:
        if not self.client:
            return []

        try:
            value, _ = self.client.get(self.ETCD_KEY)
            if value:
                return json.loads(value.decode('utf-8'))
        except json.JSONDecodeError:
            self.logger.error("Data in etcd is not valid JSON.")
        except Exception as e:
            self.logger.error(f"Failed to read commands from etcd: {e}")
            
        return []