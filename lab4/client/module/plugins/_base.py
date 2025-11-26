from abc import ABC, abstractmethod


class BasePlugin(ABC):
    @abstractmethod
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def run(self) -> float | None:
        pass

    @abstractmethod
    def cleanup(self):
        pass
