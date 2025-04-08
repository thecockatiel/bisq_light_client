from collections.abc import Callable, Collection
from concurrent.futures import Future
from typing import TYPE_CHECKING, Tuple
import threading
import random
from datetime import datetime, timedelta

from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.hash import get_32_byte_hash
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.core.network.p2p.network_not_ready_exception import NetworkNotReadyException
from bisq.core.network.p2p.peers.broadcast_handler import BroadcastHandler
from bisq.core.network.p2p.prefixed_sealed_and_signed_message import PrefixedSealedAndSignedMessage
from bisq.core.network.p2p.storage.messages.add_data_message import AddDataMessage
from bisq.core.network.p2p.storage.payload.mailbox_storage_payload import MailboxStoragePayload
from bisq.core.network.p2p.storage.payload.protected_mailbox_storage_entry import ProtectedMailboxStorageEntry
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.network.utils.capability_utils import CapabilityUtils
from utils.concurrency import AtomicInt, ThreadSafeSet
from bisq.core.network.p2p.mailbox.mailbox_message_list import MailboxMessageList
from bisq.core.network.p2p.mailbox.mailbox_item import MailboxItem
from utils.formatting import readable_file_size
from utils.preconditions import check_argument
from utils.time import get_time_ms


if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.core.network.p2p.messaging.decrypted_mailbox_listener import (
        DecryptedMailboxListener,
    )
    from bisq.core.network.p2p.network.network_node import NetworkNode
    from bisq.core.network.p2p.peers.peer_manager import PeerManager
    from bisq.core.network.p2p.storage.p2p_data_storage import P2PDataStorage
    from utils.clock import Clock
    from bisq.core.network.crypto.encryption_service import EncryptionService
    from bisq.core.network.p2p.mailbox.ignored_mailbox_service import (
        IgnoredMailboxService,
    )
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.network.p2p.send_mailbox_message_listener import SendMailboxMessageListener
    from bisq.common.crypto.sig import DSA

logger = get_logger(__name__)

class MailboxMessageService:
    REPUBLISH_DELAY_SEC = 120  # 2 minutes in seconds

    def __init__(
        self,
        network_node: "NetworkNode",
        peer_manager: "PeerManager",
        p2p_data_storage: "P2PDataStorage",
        encryption_service: "EncryptionService",
        ignored_mailbox_service: "IgnoredMailboxService",
        persistence_manager: "PersistenceManager[MailboxMessageList]",
        key_ring: "KeyRing",
        clock: "Clock",
        republish_mailbox_entries: bool,
    ) -> None:

        self.network_node = network_node
        self.peer_manager = peer_manager
        self.p2p_data_storage = p2p_data_storage
        self.encryption_service = encryption_service
        self.ignored_mailbox_service = ignored_mailbox_service
        self.persistence_manager: "PersistenceManager[MailboxMessageList]" = (
            persistence_manager
        )
        self.key_ring = key_ring
        self.clock = clock
        self.republish_mailbox_entries = republish_mailbox_entries

        self.decrypted_mailbox_listeners: ThreadSafeSet["DecryptedMailboxListener"] = (
            ThreadSafeSet()
        )
        self.mailbox_message_list: "MailboxMessageList" = MailboxMessageList()
        self.mailbox_items_by_uid: dict[str, "MailboxItem"] = {}

        self.is_bootstrapped: bool = False
        self._all_services_initialized: bool = False
        self._init_after_bootstrapped: bool = False

        self.persistence_manager.initialize(
            self.mailbox_message_list, PersistenceManagerSource.PRIVATE_LOW_PRIO
        )

    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        def process_persisted(persisted: "MailboxMessageList"):
            num_items_per_day: dict[str, Tuple[AtomicInt, list[int]]] = {}
            total_size = AtomicInt(0)

            # We sort by creation date and limit to max 3000 entries, so the oldest items get skipped even if TTL
            # is not reached. 3000 items is about 60 MB with max size of 20kb supported for storage. NOTE: comment needs to be checked for python implementation
            sorted_items = sorted(
                persisted,
                key=lambda x: x.protected_mailbox_storage_entry.creation_time_stamp,
                reverse=True
            )
            
            sorted_items = [mailbox_item for mailbox_item in sorted_items if (not mailbox_item.is_expired(self.clock) and mailbox_item.uid not in self.mailbox_items_by_uid)]
            # get first 3000 items
            sorted_items = sorted_items[:3000]
            
            for mailbox_item in sorted_items:
                protected_entry = mailbox_item.protected_mailbox_storage_entry
                serialized_size = protected_entry.to_proto_message().ByteSize()

                # Usual size is 3-4kb. A few are about 15kb and very few are larger and about 100kb or
                # more (probably attachments in disputes)
                date = datetime.fromtimestamp(protected_entry.creation_time_stamp / 1000)
                day = date.strftime("%b %d") # same as doing date.substring(4, 10) of java
                
                if day not in num_items_per_day:
                    num_items_per_day[day] = (AtomicInt(0), [])
                stat = num_items_per_day[day]
                stat[0].get_and_increment()
                stat[1].append(serialized_size)

                # We only keep small items, to reduce the potential impact of missed remove messages.
                # E.g. if a seed at a longer restart period missed the remove messages, then when loading from
                # persisted data the messages, they would add those again and distribute then later at requests to peers.
                # Those outdated messages would then stay in the network until TTL triggers removal.
                # By not applying large messages we reduce the impact of such cases at costs of extra loading costs if the message is still alive.
                if serialized_size < 20_000:
                    self.mailbox_items_by_uid[mailbox_item.uid] = mailbox_item
                    self.mailbox_message_list.append(mailbox_item)
                    total_size.get_and_add(serialized_size)

                    # We add it to our map so that it get added to the excluded key set we send for
                    # the initial data requests. So that helps to lower the load for mailbox messages at
                    # initial data requests.
                    self.p2p_data_storage.add_protected_mailbox_storage_entry_to_map(
                        protected_entry
                    )
                else:
                    logger.info(
                        f"Ignoring large persisted mailboxItem. If still valid will reload from seed nodes. "
                        f"Size={readable_file_size(serialized_size)}; date={date}; "
                        f"sender={protected_entry.mailbox_storage_payload.prefixed_sealed_and_signed_message.sender_node_address}"
                    )

            per_day = []
            for day in sorted(num_items_per_day.keys()):
                stats = num_items_per_day[day]
                total = sum(stats[1])
                large_items = [readable_file_size(s) for s in stats[1] if s > 20000]
                large_msg_info = f"; Large messages: {large_items}" if large_items else ""
                
                per_day.append(
                    f"{day}: Num messages: {stats[0]}; Total size: "
                    f"{readable_file_size(total)}{large_msg_info}"
                )

            logger.info(
                f"Loaded {len(self.mailbox_message_list)} persisted mailbox messages with "
                + f"{readable_file_size(total_size.get())}.\nPer day distribution:\n"
                + '\n'.join(per_day)
            )

            self.request_persistence()
            complete_handler()

        self.persistence_manager.read_persisted(process_persisted, complete_handler)


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Wait until all services are ready to avoid edge cases as in https://github.com/bisq-network/bisq/issues/6367
    def on_all_services_initialized(self):
        self._all_services_initialized = True
        self._init()

    # We don't listen on requestDataManager directly as we require the correct
    # order of execution. The p2pService is handling the correct order of execution and we get called
    # directly from there.
    def on_bootstrapped(self):
        if not self.is_bootstrapped:
            self.is_bootstrapped = True
    
    # second stage starup for MailboxMessageService ... apply existing messages to their modules
    def init_after_bootstrapped(self):
        self._init_after_bootstrapped = True
        self._init()

    def _init(self):
        if self._all_services_initialized and self._init_after_bootstrapped:
            # Only now we start listening and processing. The p2p_data_storage is our cache for data
            # we have received after the hidden service was ready.
            self.add_hash_map_changed_listener()
            self.on_added(self.p2p_data_storage.map.values())
            self.maybe_republish_mailbox_messages()

    def send_encrypted_mailbox_message(
        self,
        peer: "NodeAddress",
        peers_pub_key_ring: "PubKeyRing",
        mailbox_message: "MailboxMessage",
        send_mailbox_message_listener: "SendMailboxMessageListener"
    ):
        if peers_pub_key_ring is None:
            logger.debug("send_encrypted_mailbox_message: peers_pub_key_ring is None. Ignoring the call.")
            return
 
        assert peer is not None, "peer node address must not be None (send_encrypted_mailbox_message)"
        assert self.network_node.node_address_property.value is not None, "My node address must not be None at send_encrypted_mailbox_message"
        check_argument(self.key_ring.pub_key_ring != peers_pub_key_ring, "We got own keyring instead of that from peer")

        if not self.is_bootstrapped:
            raise NetworkNotReadyException()

        if not self.network_node.get_all_connections():
            send_mailbox_message_listener.on_fault(
                "There are no P2P network nodes connected. Please check your internet connection."
            )
            return

        if CapabilityUtils.capability_required_and_capability_not_supported(peer, mailbox_message, self.peer_manager):
            send_mailbox_message_listener.on_fault(
                "We did not send the EncryptedMailboxMessage because the peer does not support the capability."
            )
            return

        try:
            encrypted_data = self.encryption_service.encrypt_and_sign(
                peers_pub_key_ring, 
                mailbox_message
            )
            prefixed_sealed_message = PrefixedSealedAndSignedMessage(
                sender_node_address=self.network_node.node_address_property.value,
                sealed_and_signed=encrypted_data
            )   
                
            def on_done(future: Future):
                try: 
                    future.result()
                    send_mailbox_message_listener.on_arrived()
                except Exception as e:
                    receiver_storage_public_key = peers_pub_key_ring.signature_pub_key
                    ttl = mailbox_message.get_ttl()
                    logger.trace(f"## We take TTL from {mailbox_message.__class__.__name__}. ttl={ttl}")
                    self.add_mailbox_data(
                        MailboxStoragePayload(
                            prefixed_sealed_message,
                            ttl,
                            sender_pub_key_for_add_operation=self.key_ring.signature_key_pair.public_key,
                            owner_pub_key=receiver_storage_public_key,
                        ),
                        receiver_storage_public_key,
                        send_mailbox_message_listener
                    )

            future = self.network_node.send_message(peer, prefixed_sealed_message)
            future.add_done_callback(on_done)

        except CryptoException as e:
            logger.error("send_encrypted_message failed", exc_info=e)
            send_mailbox_message_listener.on_fault(f"send_encrypted_mailbox_message failed {str(e)}")

    def remove_mailbox_msg(self, mailbox_message: "MailboxMessage"):
        """
        The mailboxMessage has been applied and we remove it from our local storage and from the network.
        
        Args:
            mailbox_message: The MailboxMessage to be removed
        """
        if self.is_bootstrapped:
            # NOTE: comment is probably wrong in python implementation:
            # We need to delay a bit to not get a ConcurrentModificationException as we might iterate over
            # mailboxMessageList while getting called.
            def delayed_removal():
                uid = mailbox_message.uid
                if uid not in self.mailbox_items_by_uid:
                    return

                # We called removeMailboxEntryFromNetwork at processMyMailboxItem,
                # but in case we have not been bootstrapped at that moment it did not get removed from the network.
                # So to be sure it gets removed we try to remove it now again.
                # In case it was removed earlier it will return early anyway inside the p2pDataStorage.
                self.remove_mailbox_entry_from_network(
                    self.mailbox_items_by_uid[uid].protected_mailbox_storage_entry
                )

                # We will get called the onRemoved handler which triggers removeMailboxItemFromMap as well.
                # But as we use the uid from the decrypted data which is not available at onRemoved we need to
                # call removeMailboxItemFromMap here. The onRemoved only removes foreign mailBoxMessages.
                logger.trace(f"## remove_mailbox_msg uid={uid}")
                self.remove_mailbox_item_from_local_store(uid)

            UserThread.execute(delayed_removal)
        else:
            # In case the network was not ready yet we try again later
            UserThread.run_after(lambda: self.remove_mailbox_msg(mailbox_message), timedelta(seconds=30))

    def get_my_decrypted_mailbox_messages(self):
        return {
            item.decrypted_message_with_pub_key
            for item in self.mailbox_items_by_uid.values()
            if item.is_mine()
        }

    def add_decrypted_mailbox_listener(self, listener: "DecryptedMailboxListener"):
        self.decrypted_mailbox_listeners.add(listener)


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // HashMapChangedListener implementation for ProtectedStorageEntry items
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_added(self, protected_storage_entries: Collection["ProtectedStorageEntry"]):
        logger.trace("## on_added")
        
        entries: set["ProtectedStorageEntry"] = set()
        
        if self.network_node.node_address_property.value is not None:  
            entries = {
                entry for entry in protected_storage_entries 
                if isinstance(entry, ProtectedMailboxStorageEntry)
            }
        
        if len(entries) > 1:
            self.threaded_batch_process_mailbox_entries(entries)
        elif len(entries) == 1:
            self.process_single_mailbox_entry(entries)

    def on_removed(self, protected_storage_entries):
        logger.trace("## on_removed")
        
        # We can only remove the foreign mailbox messages as for our own we use the uid from the decrypted
        # payload which is not available here. But own mailbox messages get removed anyway after processing
        # at the remove_mailbox_msg method.
        for entry in protected_storage_entries:
            if isinstance(entry, ProtectedMailboxStorageEntry):
                uid = entry.mailbox_storage_payload.prefixed_sealed_and_signed_message.uid
                if uid in self.mailbox_items_by_uid:
                    self.remove_mailbox_item_from_local_store(uid)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_hash_map_changed_listener(self):
        self.p2p_data_storage.add_hash_map_changed_listener(self)

    def process_single_mailbox_entry(self, protected_mailbox_storage_entries: Collection["ProtectedMailboxStorageEntry"]):
        check_argument(len(protected_mailbox_storage_entries) == 1, "entries must have exactly one entry")
        mailbox_items = list(self.get_mailbox_items(protected_mailbox_storage_entries))
        if len(mailbox_items) == 1:
            self.handle_mailbox_item(mailbox_items[0])


    # We run the batch processing of all mailbox messages we have received at startup in a thread to not block the UI.
    # For about 1000 messages decryption takes about 1 sec. # NOTE: needs to be checked in python implementation
    def threaded_batch_process_mailbox_entries(self, protected_mailbox_storage_entries: Collection["ProtectedMailboxStorageEntry"]):
        ts = get_time_ms()
        future: Future[set["MailboxItem"]] = Future()
        
        def process():
            try:
                mailbox_items = self.get_mailbox_items(protected_mailbox_storage_entries)
                logger.info(
                    f"Batch processing of {len(protected_mailbox_storage_entries)} mailbox "
                    f"entries took {get_time_ms() - ts} ms"
                )
                future.set_result(mailbox_items)
            except Exception as e:
                future.set_exception(e)

        def on_done(future: Future[set["MailboxItem"]]):
            try:
                decrypted_mailbox_message_with_entries = future.result()
                if decrypted_mailbox_message_with_entries is None:
                    raise Exception("decrypted_mailbox_message_with_entries cannot be None in batch processing future callback")
                UserThread.execute(
                    lambda: [self.handle_mailbox_item(item) for item in decrypted_mailbox_message_with_entries]
                )
            except Exception as e:
                logger.error(f"Error in batch processing: {str(e)}")
            
        future.add_done_callback(on_done)
        
        threading.Thread(
            target=process,
            name=f"process-mailbox-entry-{random.randint(0,1000)}"
        ).start()

    def get_mailbox_items(self, protected_mailbox_storage_entries: Collection["ProtectedMailboxStorageEntry"]):
        mailbox_items: set["MailboxItem"] = set()
        for entry in protected_mailbox_storage_entries:
            item = self.try_decrypt_protected_mailbox_storage_entry(entry)
            mailbox_items.add(item)
        return mailbox_items

    def try_decrypt_protected_mailbox_storage_entry(self, protected_mailbox_storage_entry: "ProtectedMailboxStorageEntry"):
        prefixed_sealed_message = (
            protected_mailbox_storage_entry.mailbox_storage_payload.prefixed_sealed_and_signed_message
        )
        sealed_and_signed = prefixed_sealed_message.sealed_and_signed
        uid = prefixed_sealed_message.uid

        if self.ignored_mailbox_service.is_ignored(uid):
            #  We had persisted a past failed decryption attempt on that message so we don't try again and return early
            return MailboxItem(protected_mailbox_storage_entry, None)

        try:
            decrypted_msg_with_pubkey = self.encryption_service.decrypt_and_verify(
                sealed_and_signed
            )
            check_argument(isinstance(decrypted_msg_with_pubkey.network_envelope, MailboxMessage), "decrypted_msg_with_pubkey's network envelope must be a MailboxMessage")
            return MailboxItem(protected_mailbox_storage_entry, decrypted_msg_with_pubkey)
        except CryptoException:
            # Expected if message was not intended for us
            # We persist those entries so at the next startup we do not need to try to decrypt it anymore
            self.ignored_mailbox_service.ignore(
                uid, 
                protected_mailbox_storage_entry.creation_time_stamp,
            )
        except ProtobufferException as e:
            logger.error(str(e), exc_info=e)

        return MailboxItem(protected_mailbox_storage_entry, None)

    def handle_mailbox_item(self, mailbox_item: "MailboxItem"):
        uid = mailbox_item.uid
        if uid not in self.mailbox_items_by_uid:
            self.mailbox_items_by_uid[uid] = mailbox_item
            self.mailbox_message_list.append(mailbox_item)
            logger.trace(
                f"## handle_mailbox_item uid={uid}\nhash="
                f"{StorageByteArray(get_32_byte_hash(mailbox_item.protected_mailbox_storage_entry.protected_storage_payload))}"
            )
            
            self.request_persistence()
        # In case we had the item already stored we still prefer to apply it again to the domain.
        # Clients need to deal with the case that they get called multiple times with the same mailbox message.
        # This happens also because peer republish certain trade messages for higher resilience. Those messages
        # will be different mailbox messages instances but have the same internal content.
        if mailbox_item.is_mine():
            self.process_my_mailbox_item(mailbox_item, uid)

    def process_my_mailbox_item(self, mailbox_item: "MailboxItem", uid: str):
        assert mailbox_item.decrypted_message_with_pub_key is not None, "mailbox_item.decrypted_message_with_pub_key must not be None at process_my_mailbox_item"
        decrypted_message_with_pub_key = mailbox_item.decrypted_message_with_pub_key
        mailbox_message: "MailboxMessage" = decrypted_message_with_pub_key.network_envelope
        sender = mailbox_message.sender_node_address
        
        logger.info(
            f"Received a {mailbox_message.__class__.__name__} mailbox message with "
            f"uid {uid} and senderAddress {sender}"
        )
        
        for listener in self.decrypted_mailbox_listeners:
            listener.on_mailbox_message_added(decrypted_message_with_pub_key, sender)

        # GH ISSUE 6367 only remove after fully initialized
        if self._all_services_initialized and self.is_bootstrapped:
            # After we notified our listeners we remove the data immediately from the network.
            # In case the client has not been ready it need to take it via get_mailbox_messages.
            # We do not remove the data from our local map at that moment. This has to be called explicitly from the
            # client after processing. In case processing fails for some reason we still have the local data which can
            # be applied after restart, but the network got cleaned from pending mailbox messages.
            self.remove_mailbox_entry_from_network(mailbox_item.protected_mailbox_storage_entry)
        else:
            logger.info("We are not bootstrapped yet, so we remove later once the mailBoxMessage got processed.")

    def add_mailbox_data(
        self,
        expirable_mailbox_storage_payload: "MailboxStoragePayload",
        receivers_public_key: "DSA.DsaKey",
        send_mailbox_message_listener: "SendMailboxMessageListener",
    ):
        if not self.is_bootstrapped:
            raise NetworkNotReadyException()

        if not self.network_node.get_all_connections():
            send_mailbox_message_listener.on_fault(
                "There are no P2P network nodes connected. "
                "Please check your internet connection."
            )
            return

        try:
            protected_mailbox_storage_entry = self.p2p_data_storage.get_mailbox_data_with_signed_seq_nr(
                expirable_mailbox_storage_payload,
                self.key_ring.signature_key_pair,
                receivers_public_key
            )

            class BroadcastListener(BroadcastHandler.Listener):
                def on_sufficiently_broadcast(self, broadcast_requests):
                    for request in broadcast_requests:
                        if not isinstance(request.message, AddDataMessage):
                            continue
                        if request.message.protected_storage_entry != protected_mailbox_storage_entry:
                            continue
                        send_mailbox_message_listener.on_stored_in_mailbox()

                def on_not_sufficiently_broadcast(self, num_completed: int, num_failed: int):
                    send_mailbox_message_listener.on_fault(
                        f"Message was not sufficiently broadcast.\n"
                        f"numOfCompletedBroadcasts: {num_completed}.\n"
                        f"numOfFailedBroadcast={num_failed}"
                    )

            result = self.p2p_data_storage.add_protected_storage_entry(
                protected_mailbox_storage_entry,
                self.network_node.node_address_property.value,
                BroadcastListener()
            )

            if not result:
                send_mailbox_message_listener.on_fault(
                    "Data already exists in our local database"
                )
                
                # This should only fail if there are concurrent calls to addProtectedStorageEntry with the
                # same ProtectedMailboxStorageEntry. This is an unexpected use case so if it happens we
                # want to see it, but it is not worth throwing an exception.
                logger.error(
                    "Unexpected state: adding mailbox message that already exists."
                )

        except CryptoException:
            logger.error("Signing at get_mailbox_data_with_signed_seq_nr failed.")

    def remove_mailbox_entry_from_network(self, protected_mailbox_storage_entry: "ProtectedMailboxStorageEntry") -> None:
        mailbox_storage_payload = protected_mailbox_storage_entry.mailbox_storage_payload
        receivers_pub_key = protected_mailbox_storage_entry.receivers_pub_key
        try:
            updated_entry = self.p2p_data_storage.get_mailbox_data_with_signed_seq_nr(
                mailbox_storage_payload,
                self.key_ring.signature_key_pair,
                receivers_pub_key,
            )

            hash_of_payload = StorageByteArray(get_32_byte_hash(mailbox_storage_payload))
            if hash_of_payload in self.p2p_data_storage.map:
                result = self.p2p_data_storage.remove(
                    updated_entry,
                    self.network_node.node_address_property.value
                )
                if result:
                    logger.info("Removed mailboxEntry from network")
                else:
                    logger.warning("Removing mailboxEntry from network failed")
            else:
                logger.info("The mailboxEntry was already removed earlier.")
                
        except CryptoException as e:
            logger.error(
                f"Could not remove ProtectedMailboxStorageEntry from network. Error: {str(e)}",
                exc_info=e
            )

    def maybe_republish_mailbox_messages(self) -> None:
        # We only do the republishing if option is set (default is false) to avoid that the network gets too much traffic.
        # 1000 mailbox messages are about 3 MB, so that would cause quite some load if all nodes would do that.
        # We enable it on one v2 and one v3 seed node so we gain some resilience without causing much load. In
        # emergency case we can enable it on demand at any node.
        if not self.republish_mailbox_entries:
            return

        logger.info(
            f"We will republish our persisted mailbox messages after a delay of "
            f"{MailboxMessageService.REPUBLISH_DELAY_SEC} sec."
        )
        
        logger.trace(f"## republish_mailbox_messages mailbox_items_by_uid={self.mailbox_items_by_uid.keys()}")

        def delayed_republish():
            # In addProtectedStorageEntry we break early if we have already received a remove message for that entry.
            entries_to_republish = [
                item.protected_mailbox_storage_entry
                for item in self.mailbox_items_by_uid.values()
                if not item.is_expired(self.clock)
            ]
            self.republish_in_chunks(entries_to_republish)

        UserThread.run_after(delayed_republish, timedelta(seconds=MailboxMessageService.REPUBLISH_DELAY_SEC))


    # NOTE: following comment is for java implementation
    # We republish buckets of 50 items which is about 200 kb. With 20 connections at a seed node that results in
    # 4 MB in total. For 1000 messages it takes 40 min with a 2 min delay. We do that republishing just for
    # additional resilience and as a backup in case all seed nodes would fail to prevent that mailbox messages would
    # get lost. A long delay for republishing is preferred over too much network load.
    def republish_in_chunks(self, queue: list["ProtectedMailboxStorageEntry"]) -> None:
        chunk_size = 50
        logger.info(
            f"Republish a bucket of {chunk_size} persisted mailbox messages out of {len(queue)}."
        )
        
        # Process first chunk_size items
        chunk = queue[:chunk_size]
        remaining = queue[chunk_size:]
        
        for protected_mailbox_storage_entry in chunk:
            # Broadcaster will accumulate messages in a BundleOfEnvelopes
            self.p2p_data_storage.republish_existing_protected_mailbox_storage_entry(
                protected_mailbox_storage_entry,
                self.network_node.node_address_property.value,
                None
            )

        if remaining:
            # We delay 2 minutes to not overload the network
            UserThread.run_after(
                lambda: self.republish_in_chunks(remaining),
                timedelta(seconds=MailboxMessageService.REPUBLISH_DELAY_SEC)
            )

    def remove_mailbox_item_from_local_store(self, uid: str) -> None:
        mailbox_item = self.mailbox_items_by_uid.get(uid)
        if mailbox_item is None:
            return
            
        self.mailbox_items_by_uid.pop(uid, None)
        if mailbox_item in self.mailbox_message_list:
            self.mailbox_message_list.remove(mailbox_item)
        
        logger.trace(
            f"## remove_mailbox_item_from_map uid={uid}\n"
            f"hash={StorageByteArray(get_32_byte_hash(mailbox_item.protected_mailbox_storage_entry.protected_storage_payload))}\n"
            f"mailbox_items_by_uid={self.mailbox_items_by_uid.keys()}"
        )
        
        self.request_persistence()

    def request_persistence(self) -> None:
        self.persistence_manager.request_persistence()


