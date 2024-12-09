from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.model.address_entry_context import AddressEntryContext
import proto.pb_pb2 as protobuf
from utils.concurrency import ThreadSafeSet

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.wallet.wallet import Wallet
    from bitcoinj.core.address import Address

logger = get_logger(__name__)

"""
The AddressEntries was previously stored as list, now as hashSet. We still keep the old name to reflect the
associated protobuf message.
"""

class AddressEntryList(PersistableEnvelope, PersistedDataHost):

    def __init__(self, persistence_manager: Optional["PersistenceManager[AddressEntryList]"] = None, entry_set: Optional[ThreadSafeSet["AddressEntry"]] = None):
        super().__init__()
        self.wallet: Optional["Wallet"] = None
        self.entry_set: ThreadSafeSet["AddressEntry"] = ThreadSafeSet(entry_set) or ThreadSafeSet()
        self.persistence_manager = persistence_manager
        if self.persistence_manager:
            self.persistence_manager.initialize(self, PersistenceManagerSource.PRIVATE)

    def read_persisted(self, complete_handler):
        self.persistence_manager.read_persisted(lambda persisted: self._on_read(persisted, complete_handler), complete_handler)
        
    def _on_read(self, persisted: "AddressEntryList", complete_handler: Callable):
        self.entry_set.clear()
        self.entry_set.update(persisted.entry_set)
        complete_handler()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @staticmethod
    def from_proto(proto: protobuf.AddressEntryList) -> "AddressEntryList":
        return AddressEntryList(entry_set=ThreadSafeSet(AddressEntry.from_proto(entry) for entry in proto.address_entry))
    
    def to_proto_message(self):
        entries = [entry.to_proto_message() for entry in self.entry_set]
        return protobuf.PersistableEnvelope(
            address_entry_list=protobuf.AddressEntryList(address_entry=entries)
        )
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def on_wallet_ready(self):
        # TODO
        raise NotImplementedError("maybe_add_new_address_entry not implemented")

    def add_address_entry(self, address_entry: "AddressEntry") -> None:
        entry_with_same_offer_id_and_context_exists = any(
            e.offer_id == address_entry.offer_id and e.context == address_entry.context
            for e in self.entry_set if address_entry.offer_id is not None
        )
        
        if entry_with_same_offer_id_and_context_exists:
            logger.error(f"We have an address entry with the same offer ID and context. "
                  f"We do not add the new one. address_entry={address_entry}, entry_set={self.entry_set}")
            return

        logger.info(f"add_address_entry: add new AddressEntry {address_entry}")
        if self.entry_set.add(address_entry):
            self.request_persistence()

    def swap_to_available(self, address_entry: "AddressEntry") -> None:
        if address_entry.context == AddressEntryContext.MULTI_SIG:
            logger.error(f"swap_to_available called with an address_entry with MULTI_SIG context. "
                  f"This is not permitted as we must not reuse those address entries and there are "
                  f"no redeemable funds on those addresses. "
                  f"Only the keys are used for creating the Multisig address. "
                  f"address_entry={address_entry}")
            return

        logger.info(f"swap_to_available address_entry to swap={address_entry}")
        if self.entry_set.remove(address_entry):
            self.request_persistence()

        # If we have an address entry which shared the address with another one (shared maker fee offers use case)
        # then we do not swap to available as we need to protect the address of the remaining entry.
        entry_with_same_context_exists = any(
            entry.address_string == address_entry.address_string and entry.context == address_entry.context
            for entry in self.entry_set if address_entry.address_string is not None
        )
        
        if entry_with_same_context_exists:
            return

        # no other uses of the address context remain, so make it available
        entry = AddressEntry(key_pair=address_entry.key_pair,
                            context=AddressEntryContext.AVAILABLE,
                            segwit=address_entry.segwit)
        if self.entry_set.add(entry):
            self.request_persistence()

    def swap_available_to_address_entry_with_offer_id(self, address_entry: "AddressEntry", 
                                                     context: "AddressEntryContext", 
                                                     offer_id: str) -> "AddressEntry":
        set_changed_by_remove = self.entry_set.remove(address_entry)
        new_address_entry = AddressEntry(key_pair=address_entry.key_pair, 
                                       context=context,
                                       offer_id=offer_id,
                                       segwit=address_entry.segwit)
        logger.info(f"swap_available_to_address_entry_with_offer_id new_address_entry={new_address_entry}")
        set_changed_by_add = self.entry_set.add(new_address_entry)
        
        if set_changed_by_remove or set_changed_by_add:
            self.request_persistence()
            
        return new_address_entry

    def set_coin_locked_in_multi_sig_address_entry(self, address_entry: "AddressEntry", value: int) -> None:
        if address_entry.context != AddressEntryContext.MULTI_SIG:
            logger.error("set_coin_locked_in_multi_sig_address_entry must be called only on MULTI_SIG entries")
            return

        logger.info(f"set_coin_locked_in_multi_sig_address_entry address_entry={address_entry}, value={value}")
        set_changed_by_remove = self.entry_set.remove(address_entry)
        entry = AddressEntry(key_pair=address_entry.key_pair,
                           context=address_entry.context,
                           offer_id=address_entry.offer_id,
                           coin_locked_in_multi_sig=value,
                           segwit=address_entry.segwit)
        set_changed_by_add = self.entry_set.add(entry)
        
        if set_changed_by_remove or set_changed_by_add:
            self.request_persistence()

    def request_persistence(self) -> None:
        self.persistence_manager.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def maybe_add_new_address_entry(self, tx: "Transaction"):
        # TODO
        raise NotImplementedError("maybe_add_new_address_entry not implemented")

    def is_address_not_in_entries(self, address: "Address") -> bool:
        return not any(address == entry.address for entry in self.entry_set)

    def __str__(self) -> str:
        return f"AddressEntryList{{\n     entry_set={self.entry_set}\n}}"

