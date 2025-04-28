from typing import TYPE_CHECKING, List
from bisq.common.setup.log_setup import get_ctx_logger

from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.mailbox.mailbox_message import MailboxMessage
from bisq.core.trade.protocol.trade_message import TradeMessage

if TYPE_CHECKING:
    from bisq.core.network.p2p.decrypted_message_with_pub_key import DecryptedMessageWithPubKey
    from bisq.core.network.p2p.mailbox.mailbox_message_service import MailboxMessageService
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.trade.model.bisq_v1.trade import Trade
    
     

# JAVA TODO with the redesign of mailbox messages that is not required anymore. We leave it for now as we want to minimize
# changes for the 1.5.0 release but we should clean up afterwards...

class CleanupMailboxMessagesService:
    """
    Util for removing pending mailbox messages in case the trade has been closed by the seller after confirming receipt
    and a AckMessage as mailbox message will be sent by the buyer once they go online. In that case the seller's trade
    is closed already and the TradeProtocol is not executing the message processing, thus the mailbox message would not
    be removed. To ensure that in such cases (as well other potential cases in failure scenarios) the mailbox message
    gets removed from the network we use that util.
    
    This class must not be injected as a singleton!
    """
    
    def __init__(self, p2p_service: "P2PService", mailbox_message_service: "MailboxMessageService"):
        self.logger = get_ctx_logger(__name__)
        self.p2p_service = p2p_service
        self.mailbox_message_service = mailbox_message_service

    def handle_trades(self, trades: List["Trade"]) -> None:
        # We wrap in a try catch as in failed trades we cannot be sure if expected data is set, so we could get error
        # We do not want that this escalate to the user.
        try:
            if self.p2p_service.is_bootstrapped:
                self._cleanup_mailbox_messages(trades)
            else:
                class Listener(BootstrapListener):
                    def on_data_received(self_):
                        self._cleanup_mailbox_messages(trades)
                self.p2p_service.add_p2p_service_listener(Listener())
        except Exception as e:
            self.logger.error(f"Cleanup mailbox messages failed. {repr(e)}")

    def _cleanup_mailbox_messages(self, trades: List["Trade"]) -> None:
        for message in self.mailbox_message_service.get_my_decrypted_mailbox_messages():
            self._handle_decrypted_message_with_pub_key(message, trades)

    def _handle_decrypted_message_with_pub_key(self, 
                                             decrypted_message_with_pub_key: "DecryptedMessageWithPubKey",
                                             trades: List["Trade"]) -> None:
        for trade in trades:
            if (self._is_message_for_trade(decrypted_message_with_pub_key, trade) and
                self._is_pub_key_valid(decrypted_message_with_pub_key, trade) and
                isinstance(decrypted_message_with_pub_key.network_envelope, MailboxMessage)):
                self._remove_entry_from_mailbox(decrypted_message_with_pub_key.network_envelope, trade)

    def _is_message_for_trade(self, decrypted_message_with_pub_key: "DecryptedMessageWithPubKey", 
                             trade: "Trade") -> bool:
        network_envelope = decrypted_message_with_pub_key.network_envelope
        if isinstance(network_envelope, TradeMessage):
            return self._is_my_trade_message(network_envelope, trade)
        elif isinstance(network_envelope, AckMessage):
            return self._is_my_ack_message(network_envelope, trade)
        # Instance must be TradeMessage or AckMessage
        return False

    def _remove_entry_from_mailbox(self, mailbox_message: MailboxMessage, trade: "Trade") -> None:
        self.logger.info(f"We found a pending mailbox message ({mailbox_message.__class__.__name__}) for trade {trade.get_id()}. "
                   "As the trade is closed we remove the mailbox message.")
        self.mailbox_message_service.remove_mailbox_msg(mailbox_message)

    def _is_my_trade_message(self, message: "TradeMessage", trade: "Trade") -> bool:
        return message.trade_id == trade.get_id()

    def _is_my_ack_message(self, ack_message: "AckMessage", trade: "Trade") -> bool:
        return (ack_message.source_type == AckMessageSourceType.TRADE_MESSAGE and
                ack_message.source_id == trade.get_id())

    def _is_pub_key_valid(self, decrypted_message_with_pub_key: "DecryptedMessageWithPubKey", 
                         trade: "Trade") -> bool:
        # We can only validate the peers pubKey if we have it already. If we are the taker we get it from the offer
        # Otherwise it depends on the state of the trade protocol if we have received the peers pubKeyRing already.
        peers_pub_key_ring = trade.process_model.trade_peer.pub_key_ring
        is_valid = True
        if (peers_pub_key_ring is not None and
                decrypted_message_with_pub_key.signature_pub_key != peers_pub_key_ring.signature_pub_key):
            is_valid = False
            self.logger.warning("SignaturePubKey in decryptedMessageWithPubKey does not match the SignaturePubKey we have set for our trading peer.")
        return is_valid