from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.messages.counter_currency_transfer_started_message import (
    CounterCurrencyTransferStartedMessage,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator


class SellerProcessCounterCurrencyTransferStartedMessage(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            assert isinstance(
                message, CounterCurrencyTransferStartedMessage
            ), f"Expected message type to be CounterCurrencyTransferStartedMessage but was: {message.__class__.__name__}"
            Validator.check_trade_id(self.process_model.offer_id, message)
            assert message is not None, "Message cannot be None"

            trading_peer = self.process_model.trade_peer
            trading_peer.payout_address_string = Validator.non_empty_string_of(
                message.buyer_payout_address
            )
            trading_peer.signature = message.buyer_signature

            # update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            counter_currency_tx_id = message.counter_currency_tx_id
            if counter_currency_tx_id and len(counter_currency_tx_id) < 100:
                self.trade.counter_currency_tx_id = counter_currency_tx_id

            counter_currency_extra_data = message.counter_currency_extra_data
            if counter_currency_extra_data and len(counter_currency_extra_data) < 100:
                self.trade.counter_currency_extra_data = counter_currency_extra_data

            self.trade.state_property.set(
                TradeState.SELLER_RECEIVED_FIAT_PAYMENT_INITIATED_MSG
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
