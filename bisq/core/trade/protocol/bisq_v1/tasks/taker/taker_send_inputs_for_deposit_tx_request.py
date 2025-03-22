from bisq.common.crypto.sig import Sig
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import (
    InputsForDepositTxRequest,
)
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_argument, check_not_none
from utils.time import get_time_ms

logger = get_logger(__name__)


class TakerSendInputsForDepositTxRequest(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            trade_amount = check_not_none(
                self.trade.get_amount(), "trade.get_amount must not be None"
            )
            taker_fee_tx_id = check_not_none(
                self.process_model.take_offer_fee_tx_id,
                "take_offer_fee_tx_id must not be None",
            )
            user = check_not_none(self.process_model.user, "User must not be None")
            accepted_arbitrator_addresses = user.accepted_arbitrator_addresses or []
            # We don't check arbitrators as they should vanish soon
            accepted_mediator_addresses = check_not_none(
                user.accepted_mediator_addresses,
                "Accepted mediator addresses must not be None",
            )
            accepted_refund_agent_addresses = user.accepted_refund_agent_addresses or []
            # We also don't check for refund agents yet as we don't want to restrict us too much. They are not mandatory.

            wallet_service = self.process_model.btc_wallet_service
            id = self.process_model.offer.id

            multi_sig_address_entry = wallet_service.get_address_entry(
                id, AddressEntryContext.MULTI_SIG
            )
            check_argument(
                multi_sig_address_entry,
                "MULTI_SIG address entry must have been already set here.",
            )
            taker_multi_sig_pub_key = multi_sig_address_entry.pub_key
            self.process_model.my_multi_sig_pub_key = taker_multi_sig_pub_key

            payout_address_entry = wallet_service.get_address_entry(
                id, AddressEntryContext.TRADE_PAYOUT
            )
            check_argument(
                payout_address_entry,
                "TRADE_PAYOUT multi-sig address entry must have been already set here.",
            )
            taker_payout_address_string = payout_address_entry.get_address_string()

            offer_id = self.process_model.offer_id

            # From 1.7.0 on we do not send the payment account data but only the hash.
            # For backward compatibility we still keep the fields but set it to null
            hash_of_takers_payment_account_payload = (
                ProcessModel.hash_of_payment_account_payload(
                    self.process_model.get_payment_account_payload(self.trade)
                )
            )
            # We still send the signatureOfNonce below to not get too many changes. It will be needed later but it
            # does no harm to have that data earlier.

            # Taker has to use offerId as nonce (he cannot manipulate that - so we avoid to have a challenge
            # protocol for passing the nonce we want to get signed)
            # This is used for verifying the peers account age witness
            signature_of_nonce = Sig.sign(
                self.process_model.key_ring.signature_key_pair.private_key,
                offer_id.encode("utf-8"),
            )

            burning_man_selection_height = (
                self.process_model.delayed_payout_tx_receiver_service.get_burning_man_selection_height()
            )
            self.process_model.burning_man_selection_height = (
                burning_man_selection_height
            )

            takers_payment_method_id = check_not_none(
                self.process_model.get_payment_account_payload(self.trade)
            ).payment_method_id
            request = InputsForDepositTxRequest(
                trade_id=offer_id,
                sender_node_address=self.process_model.my_node_address,
                trade_amount=trade_amount.value,
                trade_price=self.trade.get_price().get_value(),
                tx_fee=self.trade.trade_tx_fee.get_value(),
                taker_fee=self.trade.get_taker_fee().get_value(),
                is_currency_for_taker_fee_btc=self.trade.is_currency_for_taker_fee_btc,
                raw_transaction_inputs=self.process_model.raw_transaction_inputs,
                change_output_value=self.process_model.change_output_value,
                change_output_address=self.process_model.change_output_address,
                taker_multi_sig_pub_key=taker_multi_sig_pub_key,
                taker_payout_address_string=taker_payout_address_string,
                taker_pub_key_ring=self.process_model.pub_key_ring,
                taker_payment_account_payload=None,
                taker_account_id=self.process_model.account_id,
                taker_fee_tx_id=taker_fee_tx_id,
                accepted_arbitrator_node_addresses=accepted_arbitrator_addresses,
                accepted_mediator_node_addresses=accepted_mediator_addresses,
                accepted_refund_agent_node_addresses=accepted_refund_agent_addresses,
                arbitrator_node_address=self.trade.arbitrator_node_address,
                mediator_node_address=self.trade.mediator_node_address,
                refund_agent_node_address=self.trade.refund_agent_node_address,
                account_age_witness_signature_of_offer_id=signature_of_nonce,
                current_date=get_time_ms(),
                hash_of_takers_payment_account_payload=hash_of_takers_payment_account_payload,
                takers_payment_method_id=takers_payment_method_id,
                burning_man_selection_height=burning_man_selection_height,
            )

            logger.info(
                f"Send {request.__class__.__name__} with offer ID {request.trade_id} and UID {request.uid} to peer {self.trade.trading_peer_node_address}"
            )

            self.process_model.trade_manager.request_persistence()

            class Listener(SendDirectMessageListener):

                def on_arrived(self_):
                    logger.info(
                        f"{request.__class__.__name__} arrived at peer: offer ID={request.trade_id}; UID={request.uid}"
                    )
                    self.complete()

                def on_fault(self_, error_message: str):
                    logger.error(
                        f"Sending {request.__class__.__name__} failed: UID={request.uid}; peer={self.trade.trading_peer_node_address}; error={error_message}"
                    )
                    self.append_to_error_message(
                        f"Sending message failed: message={request}\nerror_message={error_message}"
                    )
                    self.failed()

            self.process_model.p2p_service.send_encrypted_direct_message(
                self.trade.trading_peer_node_address,
                self.process_model.trade_peer.pub_key_ring,
                request,
                Listener(),
            )
        except Exception as e:
            self.failed(exc=e)
