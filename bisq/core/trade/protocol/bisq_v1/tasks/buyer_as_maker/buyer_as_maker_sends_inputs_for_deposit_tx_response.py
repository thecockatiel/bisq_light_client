from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_sends_inputs_for_deposit_tx_response import (
    MakerSendsInputsForDepositTxResponse,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none, check_argument


class BuyerAsMakerSendsInputsForDepositTxResponse(MakerSendsInputsForDepositTxResponse):

    def get_prepared_deposit_tx(self):
        prepared_deposit_tx = (
            self.process_model.btc_wallet_service.get_tx_from_serialized_tx(
                self.process_model.prepared_deposit_tx
            )
        )
        # Remove witnesses from preparedDepositTx, so that the seller can still compute the final
        # tx id, but cannot publish it before providing the buyer with a signed delayed payout tx.
        # TODO: check if works as expected
        return prepared_deposit_tx.bitcoin_serialize(False)
