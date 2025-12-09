from ._base import BasePlugin
import time


class NetworkPlugin(BasePlugin):
    unit = "kB/s"
    name = "network"
    
    def __init__(self, iface: str = "enp0s3"):
        super().__init__()
        self.iface = iface
        self.prev_rx = 0
        self.prev_tx = 0
        self.prev_time = time.time()

    def initialize(self):
        self.prev_rx, self.prev_tx = self._get_bytes()
        self.prev_time = time.time()

    def run(self) -> dict | None:
        rx, tx = self._get_bytes()
        now = time.time()

        if self.prev_rx is None:
            self.prev_rx, self.prev_tx, self.prev_time = rx, tx, now
            return None

        dt = now - self.prev_time
        rx_rate = (rx - self.prev_rx) / dt  # bytes/sec
        tx_rate = (tx - self.prev_tx) / dt

        # update history
        self.prev_rx, self.prev_tx, self.prev_time = rx, tx, now

        return {
            "rx": round(rx_rate / 1024, 2),
            "tx": round(tx_rate / 1024, 2),
        }

    def _get_bytes(self):
        try:
            with open(f"/sys/class/net/{self.iface}/statistics/rx_bytes") as f:
                rx = int(f.read())
            with open(f"/sys/class/net/{self.iface}/statistics/tx_bytes") as f:
                tx = int(f.read())
            return rx, tx
        except FileNotFoundError:
            return 0, 0

    def cleanup(self):
        pass
