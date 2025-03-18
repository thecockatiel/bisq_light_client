from bisq.common.setup.log_setup import get_logger
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_request import (
    DelayedPayoutTxSignatureRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator
from utils.preconditions import check_argument, check_not_none

logger = get_logger(__name__)


class BuyerProcessDelayedPayoutTxSignatureRequest(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            request = check_not_none(self.process_model.trade_message)
            if not isinstance(request, DelayedPayoutTxSignatureRequest):
                raise IllegalStateException(
                    f"Expected DelayedPayoutTxSignatureRequest but got {request.__class__.__name__}"
                )
            Validator.check_trade_id(self.process_model.offer_id, request)
            delayed_payout_tx_as_bytes = check_not_none(request.delayed_payout_tx)
            prepared_delayed_payout_tx = (
                self.process_model.btc_wallet_service.get_tx_from_serialized_tx(
                    delayed_payout_tx_as_bytes
                )
            )
            self.process_model.prepared_delayed_payout_tx = prepared_delayed_payout_tx
            self.process_model.trade_peer.delayed_payout_tx_signature = check_not_none(
                request.delayed_payout_tx_seller_signature
            )

            # When we receive that message the taker has published the taker fee, so we apply it to the trade.
            # The takerFeeTx was sent in the first message. It should be part of DelayedPayoutTxSignatureRequest
            # but that cannot be changed due to backward compatibility issues. It is a leftover from the old trade protocol.
            self.trade.taker_fee_tx_id = self.process_model.take_offer_fee_tx_id

            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
