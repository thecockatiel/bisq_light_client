from typing import TYPE_CHECKING, List, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.exceptions.dao_disabled_exception import DaoDisabledException
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.locale.res import Res
from bisq.core.offer.offer_state import OfferState
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bisq.common.taskrunner.task import Task

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel
    from bisq.common.taskrunner.task_runner import TaskRunner

logger = get_logger(__name__)

class CreateMakerFeeTx(Task["PlaceOfferModel"]):
    def __init__(
        self, task_handler: "TaskRunner[PlaceOfferModel]", model: "PlaceOfferModel"
    ):
        super().__init__(task_handler, model)

    def run(self):
        offer = self.model.offer

        try:
            self.run_intercept_hook()

            offer_id = offer.id
            wallet_service = self.model.wallet_service

            funding_address = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.OFFER_FUNDING
            ).get_address()
            reserved_for_trade_address = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.RESERVED_FOR_TRADE
            ).get_address()
            change_address = wallet_service.get_fresh_address_entry().get_address()

            trade_wallet_service = self.model.trade_wallet_service
            
            class CreateNormalTxCallback(TxBroadcasterCallback):
                def on_success(self_, transaction: "Transaction"):
                    # we delay one render frame to be sure we don't get called before the method call has
                    # returned (tradeFeeTx would be null in that case)
                    UserThread.execute(lambda: self._on_success(transaction))
                    
                def on_failure(self_, exception: Exception):
                    self._on_failure(exception)

            if offer.is_currency_for_maker_fee_btc:
                fee_receiver = self.model.btc_fee_receiver_service.get_address()
                trade_wallet_service.create_btc_trading_fee_tx(
                    funding_address=funding_address,
                    reserved_for_trade_address=reserved_for_trade_address,
                    change_address=change_address,
                    reserved_funds_for_offer=self.model.reserved_funds_for_offer,
                    use_savings_wallet=self.model.use_savings_wallet,
                    trading_fee=offer.maker_fee,
                    tx_fee=offer.tx_fee,
                    fee_receiver_address=fee_receiver,
                    do_broadcast=True,
                    callback=CreateNormalTxCallback(),
                )
            else:
                bsq_wallet_service = self.model.bsq_wallet_service
                prepared_burn_fee_tx = bsq_wallet_service.get_prepared_trade_fee_tx(
                    offer.maker_fee
                )
                tx_with_bsq_fee = trade_wallet_service.complete_bsq_trading_fee_tx(
                    prepared_bsq_tx=prepared_burn_fee_tx,
                    funding_address=funding_address,
                    reserved_for_trade_address=reserved_for_trade_address,
                    change_address=change_address,
                    reserved_funds_for_offer=self.model.reserved_funds_for_offer,
                    use_savings_wallet=self.model.use_savings_wallet,
                    tx_fee=offer.tx_fee,
                )

                signed_tx = bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
                    tx_with_bsq_fee
                )
                WalletService.check_all_script_signatures_for_tx(signed_tx)
                bsq_wallet_service.commit_tx(signed_tx, TxType.PAY_TRADE_FEE)
                # We need to create another instance, otherwise the tx would trigger an invalid state exception
                # if it gets committed 2 times
                trade_wallet_service.commit_tx(
                    trade_wallet_service.get_cloned_transaction(signed_tx)
                )
                
                class CreateBsqTxCallback(TxBroadcasterCallback):
                    def on_success(self_, transaction):
                        return self._on_success(transaction, True)
                    
                    def on_failure(self_, exception):
                        logger.error(exception, exc_info=exception)
                        offer.error_message = ("An error occurred.\n"
                                               "Error message:\n"
                                               f"{exception}")
                        self.failed(exc=exception)

                # We use a short timeout as there are issues with BSQ txs. See comment in TxBroadcaster
                bsq_wallet_service.broadcast_tx(
                    signed_tx, CreateBsqTxCallback(), timeout=1
                )

        except Exception as e:
            if isinstance(e, DaoDisabledException):
                offer.error_message = (
                    "You cannot pay the trade fee in BSQ at the moment because the DAO "
                    "features have been disabled due technical problems. Please use the "
                    "BTC fee option until the issues are resolved. For more information "
                    "please visit the Bisq Forum."
                )
            else:
                offer.error_message = f"An error occurred.\nError message:\n{e}"

            self.failed(exc=e)

    def _on_success(self, transaction: "Transaction", bsq = False):
        if transaction is None:
            logger.warning("Got success callback with transaction being None")
            return
        
        if self.completed:
            logger.warning("Got success callback after timeout triggered complete()")
            return
        
        offer = self.model.offer
        offer_id = offer.id
        wallet_service = self.model.wallet_service

        offer.set_offer_fee_payment_tx_id(transaction.get_tx_id())
        self.model.transaction = transaction
        if bsq:
            logger.debug(f"onSuccess, offerId={offer_id}, OFFER_FUNDING")
        wallet_service.swap_trade_entry_to_available_entry(
            offer_id, AddressEntryContext.OFFER_FUNDING
        )
        if bsq:
            logger.debug(f"Successfully sent tx with id {transaction.get_tx_id()}")

        offer.state = OfferState.OFFER_FEE_PAID
        self.complete()

    def _on_failure(self, exception: Exception):
        if not self.completed:
            self.failed(exc=exception)
        else:
            logger.warning("Got failure callback after timeout triggered complete()")
