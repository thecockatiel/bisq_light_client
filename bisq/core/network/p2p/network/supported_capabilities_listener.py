from abc import ABC, abstractmethod

class SupportedCapabilitiesListener(ABC):
    
    @abstractmethod
    def on_changed(self, supported_capabilities):
        pass