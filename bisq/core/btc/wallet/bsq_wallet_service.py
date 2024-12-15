from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction


# TODO
class BsqWalletService(WalletService, DaoStateListener):

    def add_wallet_transactions_change_listener(self, listener: Callable[[], None]):
        pass

    def get_available_balance(self) -> Coin:
        return Coin.ZERO()

    def get_prepared_trade_fee_tx(self) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_trade_fee_tx Not implemented yet"
        )

    def sign_tx_and_verify_no_dust_outputs(self, tx: "Transaction") -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.sign_tx_and_verify_no_dust_outputs Not implemented yet"
        )

    def commit_tx(self, tx: "Transaction") -> None:
        raise RuntimeError("BsqWalletService.commit_tx Not implemented yet")
