import importlib
from typing import List, Dict, Any
from ._base import BasePlugin
import pkgutil
import module.plugins as plugins
from ._cpu import CPUPlugin
from ._ram import RAMPlugin


class PlugingManager:
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {
            "cpu": CPUPlugin(name="cpu"),
            "memory": RAMPlugin(name="memory"),
        }

    def load_plugins(self):
        for plugin in self.plugins.values():
            plugin.initialize()

    def get_plugin(self, name: str) -> BasePlugin | None:
        if name not in self.plugins:
            return None
        return self.plugins[name]
