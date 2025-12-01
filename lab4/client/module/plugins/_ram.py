from ._base import BasePlugin
import subprocess
import shutil
import logging
try:
    import psutil
except Exception:
    psutil = None


class RAMPlugin(BasePlugin):
    unit = "%"
    name = "memory"

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def run(self) -> float | None:
        # Try `free` if available, otherwise fall back to psutil
        if shutil.which("free"):
            out = self.run_cmd(["free", "-m"])
            for line in out.splitlines():
                if line.startswith("Mem:"):
                    parts = line.split()
                    total = float(parts[1])
                    used = float(parts[2])
                    usage = (used / total) * 100.0
                    return round(usage, 2)
            return None
        if psutil is not None:
            try:
                vm = psutil.virtual_memory()
                return round(float(vm.percent), 2)
            except Exception as e:
                logging.getLogger(__name__).exception("psutil virtual_memory failed: %s", e)
        return None

    def run_cmd(self, cmd: list[str]) -> str:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except FileNotFoundError:
            raise
        except subprocess.CalledProcessError as e:
            logging.getLogger(__name__).exception("command failed: %s", e)
            return ""

    def cleanup(self):
        pass
