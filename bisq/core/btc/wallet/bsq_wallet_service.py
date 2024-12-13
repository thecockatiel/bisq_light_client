from collections.abc import Callable
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.base.coin import Coin


# TODO
class BsqWalletService(WalletService, DaoStateListener):
    
    def add_wallet_transactions_change_listener(self, listener: Callable[[], None]):
        pass

    def get_available_balance(self) -> Coin:
        return Coin.ZERO()
