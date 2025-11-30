from ._base import BasePlugin
import subprocess


class RAMPlugin(BasePlugin):
    unit = "%"
    name = "ram"

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def run(self) -> float | None:
        out = self.run_cmd(["free", "-m"])
        for line in out.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                total = float(parts[1])
                used = float(parts[2])
                usage = (used / total) * 100.0
                return round(usage, 2)
        return None

    def run_cmd(self, cmd: list[str]) -> str:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def cleanup(self):
        pass
