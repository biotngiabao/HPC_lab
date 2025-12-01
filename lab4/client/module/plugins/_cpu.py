from ._base import BasePlugin
import subprocess
import re
import shutil
import logging
try:
    import psutil
except Exception:
    psutil = None


class CPUPlugin(BasePlugin):
    unit = "%"
    name = "cpu"
    
    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def run(self) -> float | None:
        # Try to use `top` if available, otherwise fall back to psutil if installed
        if shutil.which("top"):
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
        if psutil is not None:
            try:
                # psutil.cpu_percent returns a float representing overall CPU usage
                usage = psutil.cpu_percent(interval=0.1)
                return round(float(usage), 2)
            except Exception as e:
                logging.getLogger(__name__).exception("psutil cpu_percent failed: %s", e)
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
