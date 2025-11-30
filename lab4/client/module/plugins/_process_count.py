from ._base import BasePlugin
import subprocess

class ProcessCountPlugin(BasePlugin):
    name = "process_count"

    def __init__(self):
        super().__init__()

    def run(self) -> int:
        out = self.run_cmd(["ps", "aux"])
        return len(out.splitlines()) - 1  # header excluded

    def run_cmd(self, cmd):
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()
    
    def cleanup(self):
        pass


    def initialize(self):
        pass
