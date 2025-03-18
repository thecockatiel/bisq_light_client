from abc import ABC, abstractmethod
from datetime import datetime
import uuid
from bisq.common.crypto.sig import Sig
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_response import (
    InputsForDepositTxResponse,
)
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.time import get_time_ms
from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)


class MakerSendsInputsForDepositTxResponse(TradeTask, ABC):

    @abstractmethod
    def get_prepared_deposit_tx(self) -> bytes:
        pass

    def run(self):
        try:
            self.run_intercept_hook()
            wallet_service = self.process_model.btc_wallet_service
            id = self.process_model.offer.id

            optional_multi_sig_address_entry = wallet_service.get_address_entry(
                id, AddressEntryContext.MULTI_SIG
            )
            if not optional_multi_sig_address_entry:
                raise ValueError("addressEntry must be set here.")
            maker_payout_address_entry = wallet_service.get_or_create_address_entry(
                id, AddressEntryContext.TRADE_PAYOUT
            )
            maker_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            if maker_multi_sig_pub_key != optional_multi_sig_address_entry.pub_key:
                raise ValueError(
                    f"makerMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {id}"
                )

            prepared_deposit_tx = self.get_prepared_deposit_tx()

            # Maker has to use preparedDepositTx as nonce.
            # He cannot manipulate the preparedDepositTx - so we avoid to have a challenge protocol for passing the
            # nonce we want to get signed.
            # This is used for verifying the peers account age witness
            private_key = self.process_model.key_ring.signature_key_pair.private_key
            signature_of_nonce = Sig.sign(private_key, prepared_deposit_tx)

            # From 1.7.0 on we do not send the payment account data but only the hash.
            # For backward compatibility we still keep the fields but set it to null
            hash_of_makers_payment_account_payload = (
                ProcessModel.hash_of_payment_account_payload(
                    self.process_model.get_payment_account_payload(self.trade)
                )
            )
            makers_payment_method_id = self.process_model.get_payment_account_payload(
                self.trade
            ).payment_method_id
            message = InputsForDepositTxResponse(
                trade_id=self.process_model.offer_id,
                maker_payment_account_payload=None,
                maker_account_id=self.process_model.account_id,
                maker_multi_sig_pub_key=maker_multi_sig_pub_key,
                maker_contract_as_json=self.trade.contract_as_json,
                maker_contract_signature=self.trade.maker_contract_signature,
                maker_payout_address_string=maker_payout_address_entry.get_address_string(),
                prepared_deposit_tx=prepared_deposit_tx,
                maker_inputs=self.process_model.raw_transaction_inputs,
                sender_node_address=self.process_model.my_node_address,
                account_age_witness_signature_of_prepared_deposit_tx=signature_of_nonce,
                current_date=get_time_ms(),
                lock_time=self.trade.lock_time,
                hash_of_makers_payment_account_payload=hash_of_makers_payment_account_payload,
                makers_payment_method_id=makers_payment_method_id,
            )

            self.trade.state_property.set(
                TradeState.MAKER_SENT_PUBLISH_DEPOSIT_TX_REQUEST
            )
            self.process_model.trade_manager.request_persistence()
            peers_node_address = self.trade.trading_peer_node_address
            logger.info(
                f"Send {message.__class__.__name__} to peer {peers_node_address}. "
                f"tradeId={message.trade_id}, uid={message.uid}"
            )

            class Listener(SendDirectMessageListener):
                def on_arrived(self_):
                    logger.info(
                        f"{message.__class__.__name__} arrived at peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}"
                    )
                    self.trade.state_property.set(
                        TradeState.MAKER_SAW_ARRIVED_PUBLISH_DEPOSIT_TX_REQUEST
                    )
                    self.process_model.trade_manager.request_persistence()
                    self.complete()

                def on_fault(self_, error_message: str):
                    logger.error(
                        f"{message.__class__.__name__} failed: Peer {peers_node_address}. "
                        f"tradeId={message.trade_id}, uid={message.uid}, errorMessage={error_message}"
                    )
                    self.trade.state_property.set(
                        TradeState.MAKER_SEND_FAILED_PUBLISH_DEPOSIT_TX_REQUEST
                    )
                    self.append_to_error_message(
                        f"Sending message failed: message={message}\nerrorMessage={error_message}"
                    )
                    self.process_model.trade_manager.request_persistence()
                    self.failed(error_message)

            self.process_model.p2p_service.send_encrypted_direct_message(
                peers_node_address,
                self.process_model.trade_peer.pub_key_ring,
                message,
                Listener(),
            )
        except Exception as e:
            self.failed(exc=e)
