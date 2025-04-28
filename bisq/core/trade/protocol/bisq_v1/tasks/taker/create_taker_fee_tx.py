from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.exceptions.dao_disabled_exception import DaoDisabledException
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner
    
class CreateTakerFeeTx(TradeTask):
    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            wallet_service = self.process_model.btc_wallet_service
            offer_id = self.process_model.offer.id

            # We enforce here to create a MULTI_SIG and TRADE_PAYOUT address entry to avoid that the change output would be used later
            # for those address entries. Because we do not commit our fee tx yet the change address would
            # appear as unused and therefore selected for the outputs for the MS tx.
            # That would cause incorrect display of the balance as
            # the change output would be considered as not available balance (part of the locked trade amount).
            wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.MULTI_SIG
            )
            wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.TRADE_PAYOUT
            )

            funding_address_entry = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.OFFER_FUNDING
            )
            reserved_for_trade_address_entry = (
                wallet_service.get_or_create_address_entry(
                    offer_id, AddressEntryContext.RESERVED_FOR_TRADE
                )
            )
            change_address_entry = wallet_service.get_fresh_address_entry()

            funding_address = funding_address_entry.get_address()
            reserved_for_trade_address = reserved_for_trade_address_entry.get_address()
            change_address = change_address_entry.get_address()
            trade_wallet_service = self.process_model.trade_wallet_service

            if self.trade.is_currency_for_taker_fee_btc:
                fee_receiver = self.process_model.btc_fee_receiver_service.get_address()
                transaction = trade_wallet_service.create_btc_trading_fee_tx(
                    funding_address,
                    reserved_for_trade_address,
                    change_address,
                    self.process_model.get_funds_needed_for_trade(),
                    self.process_model.use_savings_wallet,
                    self.trade.get_taker_fee(),
                    self.trade.trade_tx_fee,
                    fee_receiver,
                    False,
                    None,
                )
            else:
                prepared_burn_fee_tx = (
                    self.process_model.bsq_wallet_service.get_prepared_trade_fee_tx(
                        self.trade.get_taker_fee()
                    )
                )
                tx_with_bsq_fee = trade_wallet_service.complete_bsq_trading_fee_tx(
                    prepared_burn_fee_tx,
                    funding_address,
                    reserved_for_trade_address,
                    change_address,
                    self.process_model.get_funds_needed_for_trade(),
                    self.process_model.use_savings_wallet,
                    self.trade.trade_tx_fee,
                )
                transaction = self.process_model.bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
                    tx_with_bsq_fee
                )
                WalletService.check_all_script_signatures_for_tx(transaction)

            # We did not broadcast and commit the tx yet to avoid issues with lost trade fee in case the
            # take offer attempt failed.

            # We do not set the takerFeeTxId yet to trade as it is not published.
            self.process_model.take_offer_fee_tx_id = transaction.get_tx_id()

            self.process_model.take_offer_fee_tx = transaction
            wallet_service.swap_trade_entry_to_available_entry(
                offer_id, AddressEntryContext.OFFER_FUNDING
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            if isinstance(e, DaoDisabledException):
                self.failed(
                    "You cannot pay the trade fee in BSQ at the moment because the DAO features have been "
                    "disabled due technical problems. Please use the BTC fee option until the issues are resolved. "
                    "For more information please visit the Bisq Forum."
                )
            else:
                self.failed(exc=e)
