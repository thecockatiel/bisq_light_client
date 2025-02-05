from abc import ABC, abstractmethod


class MethodOps(ABC):

    @abstractmethod
    def parse(self) -> "MethodOps":
        pass

    @abstractmethod
    def is_for_help(self) -> bool:
        pass
