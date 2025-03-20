from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none


class SellerAsMakerFinalizesDepositTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            takers_raw_prepared_deposit_tx = check_not_none(
                self.process_model.trade_peer.prepared_deposit_tx
            )
            my_raw_prepared_deposit_tx = check_not_none(
                self.process_model.prepared_deposit_tx
            )
            takers_deposit_tx = (
                self.process_model.btc_wallet_service.get_tx_from_serialized_tx(
                    takers_raw_prepared_deposit_tx
                )
            )
            my_deposit_tx = (
                self.process_model.btc_wallet_service.get_tx_from_serialized_tx(
                    my_raw_prepared_deposit_tx
                )
            )
            num_takers_inputs = len(
                check_not_none(self.process_model.trade_peer.raw_transaction_inputs)
            )
            self.process_model.trade_wallet_service.seller_as_maker_finalizes_deposit_tx(
                my_deposit_tx, takers_deposit_tx, num_takers_inputs
            )

            self.process_model.deposit_tx = my_deposit_tx

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
