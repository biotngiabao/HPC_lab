import importlib
from typing import List, Dict, Any
from ._base import BasePlugin
import pkgutil
import module.plugins as plugins
from ._cpu import CPUPlugin
from ._ram import RAMPlugin
from ._diskio import DiskIOPlugin
from ._network import NetworkPlugin
from ._process_count import ProcessCountPlugin


class PlugingManager:
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {
            "cpu": CPUPlugin(name="cpu"),
            "memory": RAMPlugin(name="memory"),
            "diskio": DiskIOPlugin(name="diskio"),
            "network": NetworkPlugin(name="network"),
            "process_count": ProcessCountPlugin(name="process_count")
        }

    def load_plugins(self):
        for plugin in self.plugins.values():
            plugin.initialize()

    def get_plugin(self, name: str) -> BasePlugin | None:
        if name not in self.plugins:
            return None
        return self.plugins[name]
