from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.tasks.setup_payout_tx_listener import (
    SetupPayoutTxListener,
)


class BuyerSetupPayoutTxListener(SetupPayoutTxListener):

    def run(self):
        try:
            self.run_intercept_hook()
            super().run()
        except Exception as e:
            self.failed(exc=e)

    def set_state(self):
        self.trade.set_state_if_valid_transition_to(
            TradeState.BUYER_SAW_PAYOUT_TX_IN_NETWORK
        )
        self.process_model.trade_manager.request_persistence()
