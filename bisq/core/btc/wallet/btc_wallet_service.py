from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction import Transaction


# TODO
class BtcWalletService(WalletService, DaoStateListener):
    
    def get_tx_from_serialized_tx(self, serialized_tx: bytes) -> "Transaction":
        raise RuntimeError("BtcWalletService.get_tx_from_serialized_tx Not implemented yet")
    
    def get_available_address_entries(self) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_available_address_entries Not implemented yet")
    
    def get_address_entry_list_as_immutable_list(self) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_address_entry_list_as_immutable_list Not implemented yet")
    
    def get_estimated_fee_tx_vsize(self, output_values: list[Coin], tx_fee: Coin) -> int:
        raise RuntimeError("BtcWalletService.get_estimated_fee_tx_vsize Not implemented yet")

    def get_address_entries(self, context: AddressEntryContext) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_address_entries Not implemented yet")
    
    def get_or_clone_address_entry_with_offer_id(self, source_address_entry: "AddressEntry", offer_id: str) -> "AddressEntry":
        raise RuntimeError("BtcWalletService.get_or_clone_address_entry_with_offer_id Not implemented yet")