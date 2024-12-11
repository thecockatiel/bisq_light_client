from collections.abc import Callable
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener


# TODO
class BsqWalletService(WalletService, DaoStateListener):
    
    def add_wallet_transactions_change_listener(self, listener: Callable[[], None]):
        pass
