from abc import ABC, abstractmethod


class WalletTransactionsChangeListener(ABC):

    @abstractmethod
    def on_wallet_transactions_change(self):
        pass
