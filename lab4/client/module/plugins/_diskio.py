from ._base import BasePlugin
import time
from typing import Optional


class DiskIOPlugin(BasePlugin):
    """
    Monitor disk read/write throughput (kB/s) for a given block device
    by reading /proc/diskstats instead of calling iostat.

    Much faster than spawning `iostat -d 1 2` every time.
    """
    unit = "kB/s"
    name = "diskio"

    def __init__(self, device: str = "nvme0n1", sector_size: int = 512):
        super().__init__()
        self.device = device
        self.sector_size = sector_size  # bytes per sector (commonly 512)
        self._prev_read_sectors: Optional[int] = None
        self._prev_write_sectors: Optional[int] = None
        self._prev_time: Optional[float] = None

    def initialize(self):
        # Initialize previous counters so first run has a baseline
        stats = self._read_diskstats()
        if stats is not None:
            read_sec, write_sec = stats
            self._prev_read_sectors = read_sec
            self._prev_write_sectors = write_sec
            self._prev_time = time.time()

    def run(self) -> Optional[dict]:
        stats = self._read_diskstats()
        if stats is None:
            return {
                "read": 0,
                "write": 0,
            }

        read_sec, write_sec = stats
        now = time.time()

        # First call (or if something reset): store and return None
        if (
            self._prev_read_sectors is None
            or self._prev_write_sectors is None
            or self._prev_time is None
        ):
            self._prev_read_sectors = read_sec
            self._prev_write_sectors = write_sec
            self._prev_time = now
            return {
                "read": 0,
                "write": 0,
            }

        dt = now - self._prev_time
        if dt <= 0:
            return {
                "read": 0,
                "write": 0,
            }

        # Calculate deltas
        d_read = read_sec - self._prev_read_sectors
        d_write = write_sec - self._prev_write_sectors

        # Update previous state
        self._prev_read_sectors = read_sec
        self._prev_write_sectors = write_sec
        self._prev_time = now

        # Convert sectors/sec -> kB/s
        # sectors * sector_size(bytes) / dt / 1024
        read_kb_s = (d_read * self.sector_size) / dt / 1024.0
        write_kb_s = (d_write * self.sector_size) / dt / 1024.0

        return {
            "read": round(read_kb_s, 2),
            "write": round(write_kb_s, 2),
        }

    def _read_diskstats(self) -> Optional[tuple[int, int]]:
        """
        Parse /proc/diskstats and return (sectors_read, sectors_written)
        for self.device.
        """
        try:
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) < 14:
                        continue
                    # parts[2] = device name
                    if parts[2] == self.device:
                        # According to kernel docs:
                        #  3: reads completed
                        #  4: reads merged
                        #  5: sectors read
                        #  6: time reading (ms)
                        #  7: writes completed
                        #  8: writes merged
                        #  9: sectors written
                        # 10: time writing (ms)
                        sectors_read = int(parts[5])
                        sectors_written = int(parts[9])
                        return sectors_read, sectors_written
        except FileNotFoundError:
            return None

        return None

    def cleanup(self):
        pass
