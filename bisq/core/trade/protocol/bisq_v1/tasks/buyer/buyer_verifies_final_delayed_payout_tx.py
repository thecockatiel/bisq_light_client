from bisq.common.setup.log_setup import get_logger
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.trade.bisq_v1.trade_data_validation import TradeDataValidation
from bisq.core.trade.bisq_v1.trade_data_validation_exception import (
    TradeDataValidationException,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

logger = get_logger(__name__)


class BuyerVerifiesFinalDelayedPayoutTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            btc_wallet_service = self.process_model.btc_wallet_service
            final_delayed_payout_tx = self.trade.get_delayed_payout_tx()
            assert (
                final_delayed_payout_tx is not None
            ), "trade.get_delayed_payout_tx() must not be None"

            # Check again tx
            TradeDataValidation.validate_delayed_payout_tx(
                self.trade, final_delayed_payout_tx, btc_wallet_service
            )

            deposit_tx = self.trade.get_deposit_tx()
            assert deposit_tx is not None, "trade.get_deposit_tx() must not be None"
            # Now as we know the deposit tx we can also verify the input
            TradeDataValidation.validate_payout_tx_input(
                deposit_tx, final_delayed_payout_tx
            )

            input_amount = deposit_tx.outputs[0].get_value().value
            trade_tx_fee = self.trade.trade_tx_fee_as_long
            selection_height = self.process_model.burning_man_selection_height
            delayed_payout_tx_receivers = (
                self.process_model.delayed_payout_tx_receiver_service.get_receivers(
                    selection_height, input_amount, trade_tx_fee
                )
            )
            logger.info(
                f"Verify delayedPayoutTx using selectionHeight {selection_height} and receivers {delayed_payout_tx_receivers}"
            )

            lock_time = self.trade.lock_time
            buyers_delayed_payout_tx = self.process_model.trade_wallet_service.create_delayed_unsigned_payout_tx(
                deposit_tx, delayed_payout_tx_receivers, lock_time
            )

            if (
                buyers_delayed_payout_tx.get_tx_id()
                != final_delayed_payout_tx.get_tx_id()
            ):
                error_msg = "TxIds of buyersDelayedPayoutTx and finalDelayedPayoutTx must be the same."
                logger.error(
                    f"{error_msg} \nbuyersDelayedPayoutTx={buyers_delayed_payout_tx}, \nfinalDelayedPayoutTx={final_delayed_payout_tx}, "
                    f"\nBtcWalletService.chainHeight={self.process_model.btc_wallet_service.get_best_chain_height()}, "
                    f"\nDaoState.chainHeight={self.process_model.dao_facade.chain_height}, "
                    f"\nisDaoStateIsInSync={self.process_model.dao_facade.is_dao_state_ready_and_in_sync}"
                )
                raise IllegalArgumentException(error_msg)

            self.complete()
        except TradeDataValidationException as e:
            self.failed(str(e))
        except Exception as e:
            self.failed(exc=e)
