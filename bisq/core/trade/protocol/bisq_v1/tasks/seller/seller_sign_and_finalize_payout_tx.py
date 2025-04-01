from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

logger = get_logger(__name__)

class SellerSignAndFinalizePayoutTx(TradeTask):
    
    def run(self):
        try:
            self.run_intercept_hook()
            
            assert self.trade.get_amount() is not None, "trade.get_amount() must not be None"

            offer = self.trade.get_offer()
            trading_peer = self.process_model.trade_peer
            wallet_service = self.process_model.btc_wallet_service
            id = self.process_model.offer.id

            buyer_signature = trading_peer.signature
            
            assert offer.buyer_security_deposit is not None
            buyer_payout_amount = offer.buyer_security_deposit.add(self.trade.get_amount())
            seller_payout_amount = offer.seller_security_deposit

            buyer_payout_address = trading_peer.payout_address_string
            seller_payout_address = wallet_service.get_or_create_address_entry(
                id, 
                AddressEntryContext.TRADE_PAYOUT
            ).get_address_string()

            buyer_multi_sig_pub_key = trading_peer.multi_sig_pub_key
            seller_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key

            multi_sig_address_entry = wallet_service.get_address_entry(
                id,
                AddressEntryContext.MULTI_SIG
            )
            
            if not multi_sig_address_entry or seller_multi_sig_pub_key != multi_sig_address_entry.pub_key:
                # In some error edge cases it can be that the address entry is not marked (or was unmarked).
                # We do not want to fail in that case and only report a warning.
                # One case where that helped to avoid a failed payout attempt was when the taker had a power failure
                # at the moment when the offer was taken. This caused first to not see step 1 in the trade process
                # (all greyed out) but after the deposit tx was confirmed the trade process was on step 2 and
                # everything looked ok. At the payout multiSigAddressEntryOptional was not present and payout
                # could not be done. By changing the previous behaviour from fail if multiSigAddressEntryOptional
                # is not present to only log a warning the payout worked.
                logger.warning(
                    f"sellerMultiSigPubKey from AddressEntry does not match trade data. "
                    f"Trade id={id}, multi_sig_address_entry={multi_sig_address_entry}"
                )

            multi_sig_key_pair = wallet_service.get_multi_sig_key_pair(id, seller_multi_sig_pub_key)

            transaction = self.process_model.trade_wallet_service.seller_signs_and_finalizes_payout_tx(
                self.trade.deposit_tx,
                buyer_signature,
                buyer_payout_amount,
                seller_payout_amount,
                buyer_payout_address,
                seller_payout_address,
                multi_sig_key_pair,
                buyer_multi_sig_pub_key,
                seller_multi_sig_pub_key
            )

            self.trade.payout_tx = transaction
            
            self.process_model.trade_manager.request_persistence()
            
            wallet_service.reset_coin_locked_in_multi_sig_address_entry(id)
            
            self.complete()
        except Exception as e:
            self.failed(exc=e)