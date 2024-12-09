from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bitcoinj.core.transaction import Transaction


# TODO
class BtcWalletService(WalletService, DaoStateListener):
    
    def get_tx_from_serialized_tx(self, serialized_tx: bytes) -> "Transaction":
        raise RuntimeError("BtcWalletService.get_tx_from_serialized_tx Not implemented yet")
    
    def get_available_address_entries(self) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_available_address_entries Not implemented yet")
    
    def get_address_entry_list_as_immutable_list(self) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_address_entry_list_as_immutable_list Not implemented yet")