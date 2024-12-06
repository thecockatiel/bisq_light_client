from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.core.transaction import Transaction


# TODO
class BtcWalletService(WalletService, DaoStateListener):
    
    def get_tx_from_serialized_tx(self, serialized_tx: bytes) -> "Transaction":
        raise RuntimeError("BtcWalletService.get_tx_from_serialized_tx Not implemented yet")