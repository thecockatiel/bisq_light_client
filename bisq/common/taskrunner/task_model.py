
from abc import ABC, abstractmethod


# Same as TaskRunner.Model from java implementation
class TaskModel(ABC):
    @abstractmethod
    def on_complete(self):
        pass