from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_argument


class BuyerSignPayoutTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            assert (
                self.trade.get_amount() is not None
            ), "trade.get_amount() must not be None"
            assert (
                self.trade.deposit_tx is not None
            ), "trade.getDepget_deposit_txositTx() must not be None"
            offer = self.trade.get_offer()
            assert offer is not None, "offer must not be None"

            wallet_service = self.process_model.btc_wallet_service
            trade_id = self.process_model.offer.id

            buyer_payout_amount = offer.buyer_security_deposit.add(
                self.trade.get_amount()
            )
            seller_payout_amount = offer.seller_security_deposit

            buyer_payout_address = wallet_service.get_or_create_address_entry(
                trade_id, AddressEntryContext.TRADE_PAYOUT
            ).get_address_string()
            seller_payout_address = self.process_model.trade_peer.payout_address_string

            buyer_multisig_key_pair = wallet_service.get_multi_sig_key_pair(
                trade_id, self.process_model.my_multi_sig_pub_key
            )

            buyer_multisig_pubkey = self.process_model.my_multi_sig_pub_key
            check_argument(
                buyer_multisig_pubkey
                == wallet_service.get_or_create_address_entry(
                    trade_id, AddressEntryContext.MULTI_SIG
                ).pub_key,
                f"buyerMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {trade_id}"
            )
            seller_multisig_pubkey = self.process_model.trade_peer.multi_sig_pub_key

            payout_tx_signature = (
                self.process_model.trade_wallet_service.buyer_signs_payout_tx(
                    self.trade.deposit_tx,
                    buyer_payout_amount,
                    seller_payout_amount,
                    buyer_payout_address,
                    seller_payout_address,
                    buyer_multisig_key_pair,
                    buyer_multisig_pubkey,
                    seller_multisig_pubkey,
                )
            )
            self.process_model.payout_tx_signature = payout_tx_signature

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
