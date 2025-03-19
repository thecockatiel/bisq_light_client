from bisq.core.trade.protocol.bisq_v1.tasks.maker.maker_sends_inputs_for_deposit_tx_response import (
    MakerSendsInputsForDepositTxResponse,
)


class SellerAsMakerSendsInputsForDepositTxResponse(
    MakerSendsInputsForDepositTxResponse
):

    def get_prepared_deposit_tx(self):
        prepared_deposit_tx = (
            self.process_model.btc_wallet_service.get_tx_from_serialized_tx(
                self.process_model.prepared_deposit_tx
            )
        )

        for input in prepared_deposit_tx.inputs:
            # Remove signature before sending to peer as we don't want to risk that buyer could publish deposit tx
            # before we have received his signature for the delayed payout tx.
            input.script_sig = bytes()

        # TODO: check the underlaying electrum tx has indeed removed the sig from tx

        self.process_model.trade_manager.request_persistence()

        # Make sure witnesses are removed as well before sending, to cover the segwit case.
        return prepared_deposit_tx.bitcoin_serialize(False)
