from typing import TYPE_CHECKING
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

class FinalizeMediatedPayoutTx(TradeTask):
    
    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)

    def run(self):
        try:
            self.run_intercept_hook()

            deposit_tx = self.trade.get_deposit_tx()
            assert deposit_tx is not None, "deposit_tx must not be None"
            
            trade_id = self.trade.get_id()
            trading_peer = self.process_model.trade_peer
            wallet_service = self.process_model.btc_wallet_service
            
            offer = self.trade.get_offer()
            assert offer is not None, "offer must not be None"
            
            contract = self.trade.contract
            assert contract is not None, "contract must not be None"
            
            trade_amount = self.trade.get_amount()
            assert trade_amount is not None, "trade_amount must not be None"

            my_signature = self.process_model.mediated_payout_tx_signature
            assert my_signature is not None, "processModel.getTxSignatureFromMediation must not be None"
            
            peers_signature = trading_peer.mediated_payout_tx_signature
            assert peers_signature is not None, "tradingPeer.getTxSignatureFromMediation must not be None"

            is_my_role_buyer = contract.is_my_role_buyer(self.process_model.pub_key_ring)
            buyer_signature = my_signature if is_my_role_buyer else peers_signature
            seller_signature = peers_signature if is_my_role_buyer else my_signature

            total_payout_amount = offer.buyer_security_deposit.add(trade_amount).add(offer.seller_security_deposit)
            buyer_payout_amount = Coin.value_of(self.process_model.buyer_payout_amount_from_mediation)
            seller_payout_amount = Coin.value_of(self.process_model.seller_payout_amount_from_mediation)
            check_argument(total_payout_amount == buyer_payout_amount.add(seller_payout_amount),
                f"Payout amount does not match buyerPayoutAmount={buyer_payout_amount.to_friendly_string()}; sellerPayoutAmount={seller_payout_amount}"
)
            my_payout_address = wallet_service.get_or_create_address_entry(trade_id, AddressEntryContext.TRADE_PAYOUT).get_address_string()
            peers_payout_address = trading_peer.payout_address_string
            buyer_payout_address = my_payout_address if is_my_role_buyer else peers_payout_address
            seller_payout_address = peers_payout_address if is_my_role_buyer else my_payout_address

            my_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            peers_multi_sig_pub_key = trading_peer.multi_sig_pub_key
            buyer_multi_sig_pub_key = my_multi_sig_pub_key if is_my_role_buyer else peers_multi_sig_pub_key
            seller_multi_sig_pub_key = peers_multi_sig_pub_key if is_my_role_buyer else my_multi_sig_pub_key

            multi_sig_key_pair = wallet_service.get_multi_sig_key_pair(trade_id, my_multi_sig_pub_key)

            address_entry_pub_key = wallet_service.get_or_create_address_entry(trade_id, AddressEntryContext.MULTI_SIG).pub_key
            check_argument(my_multi_sig_pub_key == address_entry_pub_key,
                f"myMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {trade_id}")

            transaction = self.process_model.trade_wallet_service.finalize_mediated_payout_tx(
                deposit_tx,
                buyer_signature,
                seller_signature,
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

            wallet_service.reset_coin_locked_in_multi_sig_address_entry(trade_id)

            self.complete()
        except Exception as e:
            self.failed(exc=e)
