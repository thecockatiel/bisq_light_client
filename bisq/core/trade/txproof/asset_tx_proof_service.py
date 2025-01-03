from abc import ABC, abstractmethod


class AssetTxProofService(ABC):

    @abstractmethod
    def on_all_services_initialized(self):
        pass

    @abstractmethod
    def shut_down(self):
        pass
