from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner



class SignMediatedPayoutTx(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            trading_peer = self.process_model.trade_peer
            if self.process_model.mediated_payout_tx_signature is not None:
                self.logger.warning(
                    "process_model.get_tx_signature_from_mediation is already set"
                )

            trade_id = self.trade.get_id()
            wallet_service = self.process_model.btc_wallet_service
            deposit_tx = self.trade.deposit_tx
            offer = self.trade.get_offer()
            trade_amount = self.trade.get_amount()
            contract = self.trade.contract

            assert deposit_tx is not None, "trade.get_deposit_tx() must not be None"
            assert offer is not None, "offer must not be None"
            assert trade_amount is not None, "trade_amount must not be None"
            assert contract is not None, "contract must not be None"

            total_payout_amount = offer.buyer_security_deposit.add(trade_amount).add(
                offer.seller_security_deposit
            )
            buyer_payout_amount = Coin.value_of(
                self.process_model.buyer_payout_amount_from_mediation
            )
            seller_payout_amount = Coin.value_of(
                self.process_model.seller_payout_amount_from_mediation
            )

            check_argument(
                total_payout_amount == buyer_payout_amount.add(seller_payout_amount),
                (
                    f"Payout amount does not match buyer_payout_amount={buyer_payout_amount.to_friendly_string()}; "
                    f"seller_payout_amount={seller_payout_amount}"
                ),
            )

            is_my_role_buyer = contract.is_my_role_buyer(
                self.process_model.pub_key_ring
            )

            my_payout_address = wallet_service.get_or_create_address_entry(
                trade_id, AddressEntryContext.TRADE_PAYOUT
            ).get_address_string()
            peers_payout_address = trading_peer.payout_address_string
            buyer_payout_address = (
                my_payout_address if is_my_role_buyer else peers_payout_address
            )
            seller_payout_address = (
                peers_payout_address if is_my_role_buyer else my_payout_address
            )

            my_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            peers_multi_sig_pub_key = trading_peer.multi_sig_pub_key
            buyer_multi_sig_pub_key = (
                my_multi_sig_pub_key if is_my_role_buyer else peers_multi_sig_pub_key
            )
            seller_multi_sig_pub_key = (
                peers_multi_sig_pub_key if is_my_role_buyer else my_multi_sig_pub_key
            )

            my_multi_sig_key_pair = wallet_service.get_multi_sig_key_pair(
                trade_id, my_multi_sig_pub_key
            )

            check_argument(
                my_multi_sig_pub_key
                == wallet_service.get_or_create_address_entry(
                    trade_id, AddressEntryContext.MULTI_SIG
                ).pub_key,
                f"my_multi_sig_pub_key from AddressEntry must match the one from the trade data. trade id = {trade_id}",
            )

            mediated_payout_tx_signature = (
                self.process_model.trade_wallet_service.sign_mediated_payout_tx(
                    deposit_tx,
                    buyer_payout_amount,
                    seller_payout_amount,
                    buyer_payout_address,
                    seller_payout_address,
                    my_multi_sig_key_pair,
                    buyer_multi_sig_pub_key,
                    seller_multi_sig_pub_key,
                )
            )

            self.process_model.mediated_payout_tx_signature = (
                mediated_payout_tx_signature
            )
            self.process_model.trade_manager.request_persistence()

            self.complete()

        except Exception as e:
            self.failed(exc=e)
