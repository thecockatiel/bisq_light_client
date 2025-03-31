from abc import abstractmethod
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from utils.preconditions import check_not_none
from bisq.core.btc.listeners.address_confidence_listener import AddressConfidenceListener

if TYPE_CHECKING:
    from utils.data import SimplePropertyChangeEvent
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bisq.common.taskrunner.task_runner import TaskRunner
    from bisq.core.trade.model.bisq_v1.trade import Trade

logger = get_logger(__name__)

class SetupPayoutTxListener(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", model: "Trade"):
        super().__init__(task_handler, model)
        self.trade_state_unsub: Optional[Callable[[], None]] = None
        self.confidence_listener: "AddressConfidenceListener" = None

    @abstractmethod
    def set_state(self) -> None:
        pass

    def run(self) -> None:
        try:
            self.run_intercept_hook()
            if not self.trade.is_payout_published:
                wallet_service = self.process_model.btc_wallet_service
                trade_id = self.process_model.offer.id
                address = wallet_service.get_or_create_address_entry(trade_id, AddressEntryContext.TRADE_PAYOUT).get_address()

                deposit_tx_confidence = check_not_none(wallet_service.get_confidence_for_tx_id(self.trade.deposit_tx_id), "deposit_tx_confidence must not be None")
                # check if the payout already happened (ensuring it was > deposit block height, see GH #5725)
                confidence = wallet_service.get_confidence_for_address_from_block_height(
                    address,
                    deposit_tx_confidence.appeared_at_chain_height
                )
                
                if self._is_in_network(confidence):
                    self._apply_confidence(confidence)
                else:
                    class ConfidenceListener(AddressConfidenceListener):
                        def on_transaction_confidence_changed(self_, conf: "TransactionConfidence"):
                            if self._is_in_network(conf):
                                self._apply_confidence(conf)
                    
                    self.confidence_listener = ConfidenceListener(address)
                    
                    wallet_service.add_address_confidence_listener(self.confidence_listener)

                    def on_state_changed(e: "SimplePropertyChangeEvent[TradeState]"):
                        if self.trade.is_payout_published:
                            self.process_model.btc_wallet_service.reset_coin_locked_in_multi_sig_address_entry(self.trade.get_id())
                            UserThread.execute(self._unsubscribe)

                    self.trade_state_unsub = self.trade.state_property.add_listener(on_state_changed)
                    
            # we complete immediately, our object stays alive because the balanceListener is stored in the WalletService
            self.complete()
        except Exception as e:
            self.failed(exc=e)

    def _apply_confidence(self, confidence: "TransactionConfidence") -> None:
        if self.trade.payout_tx is None:
            wallet_tx = self.process_model.trade_wallet_service.get_wallet_tx(confidence.tx_id)
            self.trade.payout_tx = wallet_tx
            self.process_model.trade_manager.request_persistence()
            WalletService.print_tx("payoutTx received from network", wallet_tx)
            self.set_state()
        else:
            logger.info(f"We had the payout tx already set. tradeId={self.trade.get_id()}, state={self.trade.get_trade_state()}")

        self.process_model.btc_wallet_service.reset_coin_locked_in_multi_sig_address_entry(self.trade.get_id())
        
        # need delay as it can be called inside the handler before the listener and tradeStateSubscription are actually set.
        UserThread.execute(self._unsubscribe)

    def _is_in_network(self, confidence: "TransactionConfidence") -> bool:
        return (confidence is not None and
                (confidence.confidence_type == TransactionConfidenceType.BUILDING or
                 confidence.confidence_type == TransactionConfidenceType.PENDING))

    def _unsubscribe(self) -> None:
        if self.trade_state_unsub is not None:
            self.trade_state_unsub()

        if self.confidence_listener is not None:
            self.process_model.btc_wallet_service.remove_address_confidence_listener(self.confidence_listener)
