from abc import ABC, abstractmethod


class BisqSetupListener(ABC):

    def on_init_p2p_network(self):
        pass

    def on_init_wallet(self):
        pass

    def on_request_wallet_password(self):
        pass

    @abstractmethod
    def on_setup_complete(self):
        pass
