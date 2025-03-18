from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_argument, check_not_none
from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)


class BuyerFinalizesDelayedPayoutTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            btc_wallet_service = self.process_model.btc_wallet_service
            trade_id = self.process_model.offer.id
            prepared_deposit_tx = btc_wallet_service.get_tx_from_serialized_tx(
                self.process_model.prepared_deposit_tx
            )
            prepared_delayed_payout_tx = check_not_none(
                self.process_model.prepared_delayed_payout_tx
            )

            buyer_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            check_argument(
                buyer_multi_sig_pub_key
                == btc_wallet_service.get_or_create_address_entry(
                    trade_id, AddressEntryContext.MULTI_SIG
                ).pub_key,
                f"buyerMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {trade_id}",
            )
            seller_multi_sig_pub_key = self.process_model.trade_peer.multi_sig_pub_key

            buyer_signature = self.process_model.delayed_payout_tx_signature
            seller_signature = self.process_model.trade_peer.delayed_payout_tx_signature

            signed_delayed_payout_tx = self.process_model.trade_wallet_service.finalize_unconnected_delayed_payout_tx(
                prepared_delayed_payout_tx,
                buyer_multi_sig_pub_key,
                seller_multi_sig_pub_key,
                buyer_signature,
                seller_signature,
                prepared_deposit_tx.outputs[0].get_value(),
            )

            self.trade.apply_delayed_payout_tx_bytes(
                signed_delayed_payout_tx.bitcoin_serialize()
            )
            logger.info(
                f"DelayedPayoutTxBytes = {bytes_as_hex_string(self.trade.delayed_payout_tx_bytes)}",
            )

            self.complete()
        except Exception as e:
            self.failed(exc=e)
