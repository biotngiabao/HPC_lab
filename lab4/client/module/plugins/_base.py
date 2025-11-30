from abc import ABC, abstractmethod


class BasePlugin(ABC):
    unit: str = "N/A"
    name: str = "base"

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def run(self) -> float | None:
        pass

    @abstractmethod
    def cleanup(self):
        pass
