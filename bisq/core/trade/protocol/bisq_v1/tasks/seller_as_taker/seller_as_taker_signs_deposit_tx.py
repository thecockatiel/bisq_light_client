from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument, check_not_none

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner


class SellerAsTakerSignsDepositTx(TradeTask):
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            seller_inputs = check_not_none(
                self.process_model.raw_transaction_inputs,
                "sellerInputs must not be None",
            )
            wallet_service = self.process_model.btc_wallet_service
            offer_id = self.process_model.offer.id

            seller_multi_sig_address_entry = wallet_service.get_address_entry(
                offer_id, AddressEntryContext.MULTI_SIG
            )
            check_argument(
                seller_multi_sig_address_entry is not None,
                "seller_multi_sig_address_entry must be present",
            )
            seller_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            check_argument(
                seller_multi_sig_pub_key == seller_multi_sig_address_entry.pub_key,
                f"seller_multi_sig_address_entry from AddressEntry must match the one from the trade data. trade id = {offer_id}",
            )

            seller_input = Coin.value_of(sum(input.value for input in seller_inputs))

            total_fee = self.trade.trade_tx_fee.multiply(
                2  # Fee for deposit and payout tx
            )
            multi_sig_value = seller_input.subtract(total_fee)
            self.process_model.btc_wallet_service.set_coin_locked_in_multi_sig_address_entry(
                seller_multi_sig_address_entry, multi_sig_value.value
            )
            wallet_service.save_address_entry_list()

            offer = self.trade.get_offer()
            ms_output_amount = (
                offer.buyer_security_deposit.add(offer.seller_security_deposit)
                .add(self.trade.trade_tx_fee)
                .add(
                    check_not_none(
                        self.trade.get_amount(),
                        "trade.get_amount() must not be None at SellerAsTakerSignsDepositTx",
                    )
                )
            )

            trading_peer = self.process_model.trade_peer

            deposit_tx = self.process_model.trade_wallet_service.taker_signs_deposit_tx(
                True,
                self.process_model.prepared_deposit_tx,
                ms_output_amount,
                check_not_none(
                    trading_peer.raw_transaction_inputs,
                    "trading_peer.raw_transaction_inputs must not be None at SellerAsTakerSignsDepositTx",
                ),
                seller_inputs,
                trading_peer.multi_sig_pub_key,
                seller_multi_sig_pub_key,
            )

            # We set the deposit tx to trade once we have it published
            self.process_model.deposit_tx = deposit_tx

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            try:
                contract = self.trade.contract
                if contract is not None:
                    contract.print_diff(self.process_model.trade_peer.contract_as_json)
            except Exception as diff_exc:
                self.logger.error("Failed to print contract diff", exc_info=diff_exc)

            self.failed(exc=e)
