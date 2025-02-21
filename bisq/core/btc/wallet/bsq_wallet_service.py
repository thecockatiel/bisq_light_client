from collections.abc import Callable
from typing import TYPE_CHECKING, Iterable, Optional
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.base.coin import Coin
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction_output import TransactionOutput
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.listeners.bsq_balance_listener import BsqBalanceListener


# TODO
class BsqWalletService(WalletService, DaoStateListener):

    def __init__(
        self,
        wallets_setup: "WalletsSetup",
        preferences: "Preferences",
        fee_service: "FeeService",
    ):
        super().__init__(wallets_setup, preferences, fee_service)
        self.available_non_bsq_balance = Coin.ZERO()
        self.available_balance = Coin.ZERO()
        self.unverified_balance = Coin.ZERO()
        self.verified_balance = Coin.ZERO()
        self.unconfirmed_change_balance = Coin.ZERO()
        self.locked_for_voting_balance = Coin.ZERO()
        self.lockup_bonds_balance = Coin.ZERO()
        self.unlocking_bonds_balance = Coin.ZERO()
        self.bsq_balance_listeners = ThreadSafeSet["BsqBalanceListener"]()

    def add_wallet_transactions_change_listener(self, listener: Callable[[], None]):
        pass

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

    def is_unconfirmed_transactions_limit_hit(self) -> bool:
        raise RuntimeError(
            "BsqWalletService.is_unconfirmed_transactions_limit_hit Not implemented yet"
        )

    def add_bsq_balance_listener(self, listener: "BsqBalanceListener"):
        self.bsq_balance_listeners.add(listener)

    def remove_bsq_balance_listener(self, listener: "BsqBalanceListener"):
        self.bsq_balance_listeners.discard(listener)

    def get_prepared_send_bsq_tx(
        self,
        receiver_address: str,
        receiver_amount: Coin,
        utxo_candidates: Optional[set["TransactionOutput"]] = None,
    ) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_send_bsq_tx Not implemented yet"
        )

    def get_unused_address(self) -> "Address":
        raise RuntimeError("BsqWalletService.get_unused_address Not implemented yet")

    def get_unused_bsq_address_as_string(self) -> str:
        return "B" + self.get_unused_address()

    def get_buyers_bsq_inputs_for_bsq_swap_tx(
        self, required: Coin
    ) -> tuple[list["RawTransactionInput"], Coin]:
        raise RuntimeError(
            "BsqWalletService.get_buyers_bsq_inputs_for_bsq_swap_tx Not implemented yet"
        )

    def get_spendable_bsq_transaction_outputs(self) -> list["TransactionOutput"]:
        raise RuntimeError(
            "BsqWalletService.get_spendable_bsq_transaction_outputs Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BSQ TransactionOutputs and Transactions
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_cloned_wallet_transactions(self) -> list["Transaction"]:
        raise RuntimeError(
            "BsqWalletService.get_cloned_wallet_transactions Not implemented yet"
        )

    def get_pending_wallet_transactions_stream(self) -> Iterable["Transaction"]:
        raise RuntimeError(
            "BsqWalletService.get_pending_wallet_transactions_stream Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Blind vote tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_blind_vote_tx(self, fee: Coin, stake: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_blind_vote_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Burn fee txs
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_proposal_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_proposal_tx Not implemented yet"
        )

    def get_prepared_issuance_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_issuance_tx Not implemented yet"
        )

    def get_prepared_proof_of_burn_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_proof_of_burn_tx Not implemented yet"
        )

    def get_prepared_burn_fee_tx_for_asset_listing(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_burn_fee_tx_for_asset_listing Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lockup bond tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_lockup_tx(self, lockup_amount: "Coin") -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_lockup_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Unlock bond tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_unlock_tx(self, lockup_tx_output: "TxOutput") -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_unlock_tx Not implemented yet"
        )
