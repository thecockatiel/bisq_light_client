from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.tasks.broadcast_payout_tx import BroadcastPayoutTx


class SellerBroadcastPayoutTx(BroadcastPayoutTx):

    def run(self):
        try:
            self.run_intercept_hook()

            super().run()
        except Exception as e:
            self.failed(exc=e)

    def set_state(self):
        self.trade.state_property.value = TradeState.SELLER_PUBLISHED_PAYOUT_TX
        self.process_model.trade_manager.request_persistence()
