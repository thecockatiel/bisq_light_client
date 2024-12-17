from collections.abc import Callable
from concurrent.futures import Future
from typing import TYPE_CHECKING, Iterable, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bitcoinj.core.transaction import Transaction

logger = get_logger(__name__)

# TODO
class BtcWalletService(WalletService, DaoStateListener):

    def get_tx_from_serialized_tx(self, serialized_tx: bytes) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.get_tx_from_serialized_tx Not implemented yet"
        )

    def get_available_address_entries(self) -> list["AddressEntry"]:
        raise RuntimeError(
            "BtcWalletService.get_available_address_entries Not implemented yet"
        )

    def get_address_entry_list_as_immutable_list(self) -> list["AddressEntry"]:
        raise RuntimeError(
            "BtcWalletService.get_address_entry_list_as_immutable_list Not implemented yet"
        )

    def get_estimated_fee_tx_vsize(
        self, output_values: list[Coin], tx_fee: Coin
    ) -> int:
        raise RuntimeError(
            "BtcWalletService.get_estimated_fee_tx_vsize Not implemented yet"
        )

    def get_address_entries(self, context: AddressEntryContext) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_address_entries Not implemented yet")

    def get_or_clone_address_entry_with_offer_id(
        self, source_address_entry: "AddressEntry", offer_id: str
    ) -> "AddressEntry":
        raise RuntimeError(
            "BtcWalletService.get_or_clone_address_entry_with_offer_id Not implemented yet"
        )

    def get_or_create_address_entry(
        self, offer_id: str, context: AddressEntryContext
    ) -> "AddressEntry":
        raise RuntimeError(
            "BtcWalletService.get_or_create_address_entry Not implemented yet"
        )

    def get_fresh_address_entry(self, segwit: Optional[bool] = None) -> "AddressEntry":
        if segwit is None:
            segwit = True
        raise RuntimeError(
            "BtcWalletService.get_fresh_address_entry Not implemented yet"
        )

    def commit_tx(self, tx: "Transaction") -> None:
        raise RuntimeError("BsqWalletService.commit_tx Not implemented yet")

    def swap_trade_entry_to_available_entry(
        self, offer_id: str, context: AddressEntryContext
    ) -> None:
        raise RuntimeError(
            "BtcWalletService.swap_trade_entry_to_available_entry Not implemented yet"
        )

    def get_address_entries_for_open_offer(self) -> list[AddressEntry]:
        raise RuntimeError(
            "BtcWalletService.get_address_entries_for_open_offer Not implemented yet"
        )

    def reset_address_entries_for_open_offer(self) -> None:
        raise RuntimeError(
            "BtcWalletService.reset_address_entries_for_open_offer Not implemented yet"
        )

    def is_unconfirmed_transactions_limit_hit(self) -> bool:
        raise RuntimeError(
            "BtcWalletService.is_unconfirmed_transactions_limit_hit Not implemented yet"
        )

    def get_address_entries_for_available_balance_stream(
        self,
    ) -> Iterable[AddressEntry]:
        raise RuntimeError(
            "BtcWalletService.get_address_entries_for_available_balance_stream Not implemented yet"
        )

    def send_funds(
        self,
        from_address: str,
        to_address: str,
        receiver_amount: Coin,
        fee: Coin,
        aes_key: Optional[bytes] = None,
        context: Optional[AddressEntryContext] = None,
        memo: Optional[str] = None,
        callback: Optional[Callable[[Future["Transaction"]], None]] = None,
    ) -> str:
        raise RuntimeError("BtcWalletService.send_funds Not implemented yet")

    def reset_address_entries_for_pending_trade(self, offer_id: str) -> None:
        raise RuntimeError(
            "BtcWalletService.reset_address_entries_for_pending_trade Not implemented yet"
        )

    def recover_address_entry(
        self, offer_id: str, address: str, context: AddressEntryContext
    ) -> None:
        raise RuntimeError("BtcWalletService.recover_address_entry Not implemented yet")

    def get_arbitrator_address_entry(self) -> "AddressEntry":
        raise RuntimeError(
            "BtcWalletService.get_arbitrator_address_entry Not implemented yet"
        )
        
    def get_multi_sig_key_pair(self, trade_id: str, pub_key: bytes) -> "DeterministicKey":
        raise RuntimeError(
            "BtcWalletService.get_multi_sig_key_pair Not implemented yet"
        )

    @staticmethod
    def print_tx(trade_prefix: str, tx: "Transaction") -> None:
        logger.info(f"\n{trade_prefix}:\n{tx}")
    