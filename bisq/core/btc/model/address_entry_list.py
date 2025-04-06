from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.config.config import Config
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.script.script_type import ScriptType
import pb_pb2 as protobuf
from utils.concurrency import ThreadSafeSet
from bitcoinj.core.address import Address

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.wallet.wallet import Wallet

logger = get_logger(__name__)

"""
The AddressEntries was previously stored as list, now as hashSet. We still keep the old name to reflect the
associated protobuf message.
"""

class AddressEntryList(PersistableEnvelope, PersistedDataHost):

    def __init__(self, persistence_manager: Optional["PersistenceManager[AddressEntryList]"] = None, entry_set: Optional[ThreadSafeSet["AddressEntry"]] = None):
        super().__init__()
        self._wallet: Optional["Wallet"] = None
        self.entry_set: ThreadSafeSet["AddressEntry"] = ThreadSafeSet(entry_set)
        self.persistence_manager = persistence_manager
        if self.persistence_manager:
            self.persistence_manager.initialize(self, PersistenceManagerSource.PRIVATE)

    def read_persisted(self, complete_handler: Callable[[], None]):
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
    
    def on_wallet_ready(self, wallet: "Wallet"):
        self._wallet = wallet
        
        # TODO: check if works correctly
        if self.entry_set:
            to_be_removed = set["AddressEntry"]()
            for entry in self.entry_set:
                if entry.segwit:
                    script_type = ScriptType.P2WPKH
                else:
                    script_type = ScriptType.P2PKH
                key = wallet.find_key_from_pub_key_hash(entry.pub_key_hash, script_type)
                if key:
                    address_from_key = Address.from_key(key, script_type, Config.BASE_CURRENCY_NETWORK_VALUE.parameters)
                    # We want to ensure key and address matches in case we have address in entry available already
                    if entry.is_address_none or address_from_key == entry.get_address():
                        entry.set_deterministic_key(key)
                    else:
                        logger.error(f"We found an address entry without key but cannot apply the key as the address "
                                     f"is not matching. "
                                     f"We remove that entry as it seems it is not compatible with our wallet. "
                                     f"addressFromKey={address_from_key}, addressEntry.getAddress()={entry.get_address()}")
                        to_be_removed.add(entry)
                else:
                    logger.error(f"Key from addressEntry {entry} not found in that wallet. We remove that entry. "
                                 "This is expected at restore from seeds.")
                    to_be_removed.add(entry)
            
            for entry in to_be_removed:
                self.entry_set.discard(entry)
        else:
            # TODO: double check later if its okay to generate a segwit address here.
            # to generate a legacy address means we have to create and handle an extra wallet instance,
            # so we use segwit for now to not do that
            key = wallet.find_key_from_address(wallet.fresh_receive_address())
            self.entry_set.add(
                AddressEntry(key_pair=key, context=AddressEntryContext.ARBITRATOR, segwit=True)
            )
        
        # In case we restore from seed words and have balance we need to add the relevant addresses to our list.
        # IssuedReceiveAddresses does not contain all addresses where we expect balance so we need to listen to
        # incoming txs at blockchain sync to add the rest.
        if self._wallet.get_available_balance() > 0:
            for address in self._wallet.get_issued_receive_addresses():
                if self.is_address_not_in_entries(address):
                    key = self._wallet.find_key_from_address(address)
                    if key:
                        # Address will be derived from key in getAddress method
                        logger.info(f"Create AddressEntry for IssuedReceiveAddress. address={address}")
                        self.entry_set.add(AddressEntry(key_pair=key, context=AddressEntryContext.AVAILABLE, segwit=isinstance(address, SegwitAddress)))
                    else:
                        logger.warning(f"DeterministicKey for address {address} is None")
        
        # We add those listeners to get notified about potential new transactions and
        # add an address entry list in case it does not exist yet. This is mainly needed for restore from seed words
        # but can help as well in case the addressEntry list would miss an address where the wallet was received
        # funds (e.g. if the user sends funds to an address which has not been provided in the main UI - like from the
        # wallet details window).
 
        wallet.add_new_tx_listener(self.maybe_add_new_address_entry)
        
        self.request_persistence()

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
            entry.get_address_string() == address_entry.get_address_string() and entry.context == address_entry.context
            for entry in self.entry_set if address_entry.get_address_string() is not None
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
        for output in tx.outputs:
            if output.is_for_wallet(self._wallet):
                try:
                    address = output.get_script_pub_key().get_to_address(self._wallet.network_params)
                except:
                    address = None
                if address and self.is_address_not_in_entries(address):
                    key = self._wallet.find_key_from_address(address)
                    if key:
                        self.add_address_entry(
                            AddressEntry(
                                key_pair=key,
                                context=AddressEntryContext.AVAILABLE,
                                segwit=isinstance(address, SegwitAddress)
                            )
                        )

    def is_address_not_in_entries(self, address: "Address") -> bool:
        return not any(address == entry.get_address() for entry in self.entry_set)

    def __str__(self) -> str:
        return f"AddressEntryList{{\n     entry_set={self.entry_set}\n}}"

