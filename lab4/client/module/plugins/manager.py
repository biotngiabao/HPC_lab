import importlib
from typing import List, Dict, Any
from ._base import BasePlugin
import pkgutil
import module.plugins as plugins


class PlugingManager:
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}

    def load_plugins(self):
        for _, modname, _ in pkgutil.iter_modules(
            plugins.__path__, plugins.__name__ + "."
        ):
            module = importlib.import_module(modname)
            for attr in dir(module):
                obj = getattr(module, attr)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin
                ):
                    plugin: BasePlugin = obj(name=modname)
                    plugin.initialize()
                    self.plugins[plugin.name] = plugin

    def get_plugin(self, name: str) -> BasePlugin | None:
        if name not in self.plugins:
            return None
        return self.plugins[name]
