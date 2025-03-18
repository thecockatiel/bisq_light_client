from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none, check_argument


class BuyerAsTakerCreatesDepositTxInputs(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            tx_fee = self.trade.trade_tx_fee
            taker_input_amount = (
                check_not_none(self.trade.get_offer())
                .buyer_security_deposit.add(tx_fee)
                .add(tx_fee)  # 2 times the fee as we need it for payout tx as well
            )
            result = (
                self.process_model.trade_wallet_service.taker_creates_deposit_tx_inputs(
                    self.process_model.take_offer_fee_tx, taker_input_amount, tx_fee
                )
            )
            self.process_model.raw_transaction_inputs = result.raw_transaction_inputs
            self.process_model.change_output_value = result.change_output_value
            self.process_model.change_output_address = result.change_output_address

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
