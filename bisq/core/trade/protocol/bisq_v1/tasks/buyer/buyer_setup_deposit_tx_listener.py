from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.taskrunner.task_runner import TaskRunner
from bisq.common.user_thread import UserThread
from bisq.core.btc.listeners.address_confidence_listener import (
    AddressConfidenceListener,
)
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
from bisq.core.trade.model.trade_state import TradeState
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bitcoinj.core.address import Address
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bisq.core.trade.model.bisq_v1.trade import Trade

logger = get_logger(__name__)


class BuyerSetupDepositTxListener(TradeTask):

    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)
        self.trade_state_subscription: Optional[Callable[[], None]] = None
        self.confidence_listener: Optional[AddressConfidenceListener] = None

    def run(self):
        try:
            self.run_intercept_hook()

            if (
                self.trade.get_deposit_tx() is None
                and self.process_model.prepared_deposit_tx is not None
            ):
                wallet_service = self.process_model.btc_wallet_service
                params = wallet_service.params
                prepared_deposit_tx = Transaction(
                    params, self.process_model.prepared_deposit_tx
                )
                check_argument(
                    prepared_deposit_tx.outputs is not None
                    and len(prepared_deposit_tx.outputs) > 0,
                    "prepared_deposit_tx.outputs must not be empty",
                )
                deposit_tx_address = (
                    prepared_deposit_tx.outputs[0]
                    .get_script_pub_key()
                    .get_to_address(params)
                )

                # For buyer as maker takerFeeTxId is null
                taker_fee_tx_id = self.trade.taker_fee_tx_id
                maker_fee_tx_id = self.trade.get_offer().offer_fee_payment_tx_id
                confidence = wallet_service.get_confidence_for_address(
                    deposit_tx_address
                )
                if self._is_conf_tx_deposit_tx(
                    confidence,
                    params,
                    deposit_tx_address,
                    taker_fee_tx_id,
                    maker_fee_tx_id,
                ) and self._is_visible_in_network(confidence):
                    self._apply_confidence(confidence)
                else:

                    class MyConfidenceListener(AddressConfidenceListener):
                        def on_transaction_confidence_changed(
                            self_, confidence: "TransactionConfidence"
                        ):
                            if self._is_conf_tx_deposit_tx(
                                confidence,
                                params,
                                deposit_tx_address,
                                taker_fee_tx_id,
                                maker_fee_tx_id,
                            ) and self._is_visible_in_network(confidence):
                                self._apply_confidence(confidence)

                    self.confidence_listener = MyConfidenceListener(deposit_tx_address)
                    wallet_service.add_address_confidence_listener(
                        self.confidence_listener
                    )

                    def on_state_changed(e):
                        if self.trade.is_deposit_published:
                            self._swap_reserved_for_trade_entry()
                            # hack to remove tradeStateSubscription at callback (??)
                            UserThread.execute(self._unsubscribe_and_remove_listener)

                    self.trade_state_subscription = (
                        self.trade.state_property.add_listener(on_state_changed)
                    )

            # we complete immediately, our object stays alive because the balanceListener is stored in the WalletService
            self.complete()
        except Exception as e:
            self.failed(exc=e)

    # We check if the txIds of the inputs matches our maker fee tx and taker fee tx and if the depositTxAddress we
    # use for the confidence lookup is use as an output address.
    # This prevents that past txs which have the our depositTxAddress as input or output (deposit or payout txs) could
    # be interpreted as our deposit tx. This happened because if a bug which caused re-use of the Multisig address
    # entries and if both traders use the same key for multiple trades the depositTxAddress would be the same.
    # We fix that bug as well but we also need to avoid that past already used addresses might be taken again
    # (the Multisig flag got reverted to available in the address entry).
    def _is_conf_tx_deposit_tx(
        self,
        confidence: Optional["TransactionConfidence"],
        params: "NetworkParameters",
        deposit_tx_address: "Address",
        taker_fee_tx_id: Optional[str],
        maker_fee_tx_id: str,
    ) -> bool:
        if confidence is None:
            return False

        wallet_tx: Optional["Transaction"] = (
            self.process_model.trade_wallet_service.get_wallet_tx(
                confidence.tx_id
            )
        )

        if wallet_tx is None:
            raise ValueError(
                f"Could not find wallet tx for confidence tx. confidenceTx={confidence}"
            )

        num_input_matches = sum(
            1
            for tx_input in wallet_tx.inputs
            if tx_input.outpoint is not None
            and tx_input.outpoint.hash is not None
            and tx_input.outpoint.hash in [taker_fee_tx_id, maker_fee_tx_id]
        )

        if taker_fee_tx_id is None and num_input_matches != 1:
            logger.warning(
                f"We got a transactionConfidenceTx which does not match our inputs. "
                f"takerFeeTxId is null (valid if role is buyer as maker) and numInputMatches "
                f"is not 1 as expected (for makerFeeTxId). "
                f"numInputMatches={num_input_matches}, transactionConfidenceTx={wallet_tx}"
            )
            return False
        elif taker_fee_tx_id is not None and num_input_matches != 2:
            logger.warning(
                f"We got a transactionConfidenceTx which does not match our inputs. "
                f"numInputMatches is not 2 as expected (for makerFeeTxId and takerFeeTxId). "
                f"numInputMatches={num_input_matches}, transactionConfidenceTx={wallet_tx}"
            )
            return False

        is_output_matching = any(
            output.get_script_pub_key().get_to_address(params) == deposit_tx_address
            for output in wallet_tx.outputs
        )
        if not is_output_matching:
            logger.warning(
                f"We got a transactionConfidenceTx which does not have the depositTxAddress "
                f"as output (but as input). depositTxAddress={deposit_tx_address}, transactionConfidenceTx={wallet_tx}"
            )
        return is_output_matching

    def _apply_confidence(self, confidence: "TransactionConfidence"):
        if self.trade.get_deposit_tx() is None:
            wallet_tx: Optional[Transaction] = (
                self.process_model.trade_wallet_service.get_wallet_tx(
                    confidence.tx_id
                )
            )
            self.trade.apply_deposit_tx(wallet_tx)
            BtcWalletService.print_tx("depositTx received from network", wallet_tx)

            # We don't want to trigger the tradeStateSubscription when setting the state, so we unsubscribe before
            self._unsubscribe_and_remove_listener()
            self.trade.state_property.set(TradeState.BUYER_SAW_DEPOSIT_TX_IN_NETWORK)

            self.process_model.trade_manager.request_persistence()
        else:
            self._unsubscribe_and_remove_listener()

        self._swap_reserved_for_trade_entry()

    def _is_visible_in_network(self, confidence: "TransactionConfidence") -> bool:
        return confidence is not None and (
            confidence.confidence_type == TransactionConfidenceType.BUILDING
            or confidence.confidence_type == TransactionConfidenceType.PENDING
        )

    def _swap_reserved_for_trade_entry(self):
        self.process_model.btc_wallet_service.swap_trade_entry_to_available_entry(
            self.trade.get_id(), AddressEntryContext.RESERVED_FOR_TRADE
        )

    def _unsubscribe_and_remove_listener(self):
        if self.trade_state_subscription is not None:
            self.trade_state_subscription()
            self.trade_state_subscription = None

        if self.confidence_listener is not None:
            self.process_model.btc_wallet_service.remove_address_confidence_listener(
                self.confidence_listener
            )
            self.confidence_listener = None
