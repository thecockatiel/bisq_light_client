from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.core.transaction import Transaction
from utils.preconditions import check_argument, check_not_none


class SellerSignsDelayedPayoutTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            prepared_delayed_payout_tx = check_not_none(
                self.process_model.prepared_delayed_payout_tx
            )
            btc_wallet_service = self.process_model.btc_wallet_service
            params = btc_wallet_service.params
            prepared_deposit_tx = Transaction(
                params, self.process_model.prepared_deposit_tx
            )

            trade_id = self.process_model.offer.id

            seller_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            my_multi_sig_key_pair = btc_wallet_service.get_multi_sig_key_pair(
                trade_id, seller_multi_sig_pub_key
            )

            check_argument(
                seller_multi_sig_pub_key
                == btc_wallet_service.get_or_create_address_entry(
                    trade_id, AddressEntryContext.MULTI_SIG
                ).pub_key,
                f"sellerMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {trade_id}",
            )
            buyer_multi_sig_pub_key = self.process_model.trade_peer.multi_sig_pub_key

            delayed_payout_tx_signature = (
                self.process_model.trade_wallet_service.sign_delayed_payout_tx(
                    prepared_delayed_payout_tx,
                    prepared_deposit_tx,
                    my_multi_sig_key_pair,
                    buyer_multi_sig_pub_key,
                    seller_multi_sig_pub_key,
                )
            )

            self.process_model.delayed_payout_tx_signature = delayed_payout_tx_signature

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
