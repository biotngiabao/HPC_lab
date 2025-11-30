import importlib
import logging
from typing import Dict, List
from ._base import BasePlugin

class PlugingManager:
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.logger = logging.getLogger(__name__)

    def load_plugins(self, plugin_paths: List[str] = None):
        if not plugin_paths:
            self.logger.warning("No plugin paths provided to load.")
            return

        self.plugins = {}

        for path in plugin_paths:
            try:
                if "." not in path:
                    self.logger.error(f"Invalid plugin path format: {path}")
                    continue

                module_name, class_name = path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                plugin_cls = getattr(module, class_name)
                plugin_instance = plugin_cls()
                plugin_instance.initialize()
                if hasattr(plugin_instance, 'name'):
                    key_name = plugin_instance.name
                else:
                    key_name = class_name.lower().replace("plugin", "")
                
                self.plugins[key_name] = plugin_instance
                self.logger.info(f"Successfully loaded plugin '{key_name}' from {path}")

            except ImportError as e:
                self.logger.error(f"Error importing module for {path}: {e}")
            except AttributeError as e:
                self.logger.error(f"Class name not found in module for {path}: {e}")
            except Exception as e:
                self.logger.error(f"Failed to load plugin {path}: {e}")

    def get_plugin(self, metric_name: str) -> BasePlugin:
        return self.plugins.get(metric_name)