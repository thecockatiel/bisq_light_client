from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.trade.protocol.bisq_v1.messages.deposit_tx_message import (
    DepositTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator
from utils.preconditions import check_not_none


class SellerAsMakerProcessDepositTxMessage(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            if not isinstance(message, DepositTxMessage):
                raise IllegalStateException(
                    f"Expected DepositTxMessage but got {message.__class__.__name__}"
                )
            Validator.check_trade_id(self.process_model.offer_id, message)

            self.process_model.trade_peer.prepared_deposit_tx = check_not_none(
                message.deposit_tx_without_witnesses
            )
            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            # When we receive that message the taker has published the taker fee, so we apply it to the trade.
            # The takerFeeTx was sent in the first message. It should be part of DelayedPayoutTxSignatureRequest
            # but that cannot be changed due to backward compatibility issues. It is a leftover from the old trade protocol.
            self.trade.taker_fee_tx_id = self.process_model.take_offer_fee_tx_id

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
