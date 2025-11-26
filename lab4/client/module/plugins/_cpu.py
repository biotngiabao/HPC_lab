from ._base import BasePlugin
import subprocess
import re


class CPUPlugin(BasePlugin):
    def __init__(self, name: str):
        super().__init__(name)

    def initialize(self):
        pass

    def run(self) -> float | None:
        out = self.run_cmd(["top", "-bn1"])
        cpu_line = ""
        for line in out.splitlines():
            if "Cpu(s):" in line:
                cpu_line = line
                break

        m = re.search(r"([\d\.]+)\s+id", cpu_line)
        if not m:
            return None
        idle = float(m.group(1))
        return round(100.0 - idle, 2)

    def run_cmd(self, cmd: list[str]) -> str:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def cleanup(self):
        pass
