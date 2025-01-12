from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bitcoinj.wallet.wallet import Wallet


class WalletChangeEventListener(Callable[["Wallet"], None], ABC):
    """
    Implementors are called when the contents of the wallet changes, for instance due to receiving/sending money
    or a block chain re-organize.
    """

    @abstractmethod
    def on_wallet_changed(wallet: "Wallet"):
        """
        A callback method designed for GUI applications to refresh their transaction lists.
        This callback is invoked in the following situations:
        - A new block is received (and thus building transactions got more confidence)
        - A pending transaction is received
        - A pending transaction changes confidence due to some non-new-block related event,
            such as being announced by more peers or by a double-spend conflict being observed
        - A re-organize occurs. Call occurs only if the re-org modified any of our transactions
        - A new spend is committed to the wallet
        - The wallet is reset and all transactions removed
        When this is called you can refresh the UI contents from the wallet contents.
        It's more efficient to use this rather than onTransactionConfidenceChanged() + onReorganize()
        because you only get one callback per block rather than one per transaction per block.
        Note that this is not called when a key is added.
        Args:
                wallet (Wallet): The wallet that changed and triggered this callback
        Returns:
                None
        """
        pass

    def __call__(self, *args, **kwds):
        return self.on_wallet_changed(*args, **kwds)
