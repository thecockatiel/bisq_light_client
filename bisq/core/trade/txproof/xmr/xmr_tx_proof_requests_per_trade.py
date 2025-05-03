from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.handlers.fault_handler import FaultHandler
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.locale.res import Res
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.txproof.asset_tx_proof_requests_per_trade import (
    AssetTxProofRequestsPerTrade,
)
from bisq.core.trade.txproof.asset_tx_proof_result import AssetTxProofResult
from bisq.core.trade.txproof.xmr.xmr_tx_proof_model import XmrTxProofModel
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request import XmrTxProofRequest
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_detail import XmrTxProofRequestDetail
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_result import XmrTxProofRequestResult
from bitcoinj.base.coin import Coin
from utils.data import ObservableChangeEvent, ObservableList, SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bisq.core.user.auto_confirm_settings import AutoConfirmSettings
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.support.refund.refund_manager import RefundManager
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.support.dispute.mediation.mediation_manager import MediationManager
    from bisq.core.support.dispute.dispute import Dispute


class XmrTxProofRequestsPerTrade(AssetTxProofRequestsPerTrade):

    def __init__(
        self,
        socks5_proxy_provider: "Socks5ProxyProvider",
        auto_confirm_settings: "AutoConfirmSettings",
        trade: "Trade",
        mediation_manager: "MediationManager",
        filter_manager: "FilterManager",
        refund_manager: "RefundManager",
    ):
        self.logger = get_ctx_logger(__name__)
        self.socks5_proxy_provider = socks5_proxy_provider
        self.trade = trade
        self.auto_confirm_settings = auto_confirm_settings
        self.mediation_manager = mediation_manager
        self.filter_manager = filter_manager
        self.refund_manager = refund_manager
        self._subscriptions: list[Callable[[], None]] = []
        
        self.num_required_success_results = 0
        self.requests = set["XmrTxProofRequest"]()
        
        self.num_success_results = 0
        self.trade_state_listener: Optional[Callable[[SimplePropertyChangeEvent[TradeState]], None]] = None
        self.auto_confirm_settings_listener: Optional["AutoConfirmSettings.Listener"] = None
        self.mediation_listener: "Callable[[ObservableChangeEvent[Dispute]], None]" = None
        self.refund_listener: "Callable[[ObservableChangeEvent[Dispute]], None]" = None
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def request_from_all_services(
        self,
        result_handler: "Callable[[AssetTxProofResult], None]",
        fault_handler: "FaultHandler",
    ) -> None:
        if self.is_trade_amount_above_limit(self.trade):
            self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.TRADE_LIMIT_EXCEEDED)
            return

        if self.trade.is_payout_published:
            self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.PAYOUT_TX_ALREADY_PUBLISHED)
            return

        # We will stop all our services if the user changes the enable state in the AutoConfirmSettings
        if not self.auto_confirm_settings.enabled:
            self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.FEATURE_DISABLED)
            return

        self.add_settings_listener(result_handler)
        
        # TradeState
        self.setup_trade_state_listener(result_handler)
        # We checked initially for current trade state so no need to check again here

        # Check if mediation dispute and add listener
        mediation_disputes = self.mediation_manager.get_disputes_as_observable_list()
        if self.is_disputed(mediation_disputes):
            self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.DISPUTE_OPENED)
            return

        self.setup_mediation_listener(result_handler, mediation_disputes)

        # Check if arbitration dispute and add listener
        refund_disputes = self.refund_manager.get_disputes_as_observable_list()
        if self.is_disputed(refund_disputes):
            self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.DISPUTE_OPENED)
            return

        self.setup_arbitration_listener(result_handler, refund_disputes)

        # All good so we start
        self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.REQUESTS_STARTED)

        # We set serviceAddresses at request time. If user changes AutoConfirmSettings after request has started
        # it will have no impact on serviceAddresses and numRequiredSuccessResults.
        # Though numRequiredConfirmations can be changed during request process and will be read from
        # autoConfirmSettings at result parsing.
        service_addresses = self.auto_confirm_settings.service_addresses
        self.num_required_success_results = len(service_addresses)

        for service_address in service_addresses:
            if self.filter_manager.is_auto_conf_explorer_banned(service_address):
                self.logger.warning(f"Filtered out auto-confirmation address: {service_address}")
                continue #  #4683: filter for auto-confirm explorers

            model = XmrTxProofModel.from_trade(self.trade, service_address, self.auto_confirm_settings)
            request = XmrTxProofRequest(self.socks5_proxy_provider, model)

            self.logger.info(f"{request} created")
            self.requests.add(request)

            def handle_result(result: XmrTxProofRequestResult) -> None:
                # If we ever received an error or failed result we terminate and do not process any
                # future result anymore to avoid that we overwrite our state with success.
                if self.was_terminated():
                    return

                if self.trade.is_payout_published:
                    self.call_result_handler_and_maybe_terminate(
                        result_handler, AssetTxProofResult.PAYOUT_TX_ALREADY_PUBLISHED
                    )
                    return
                
                asset_tx_proof_result = AssetTxProofResult.ERROR
                
                if result == XmrTxProofRequestResult.PENDING:
                    # We expect repeated PENDING results with different details
                    asset_tx_proof_result = self.get_asset_tx_proof_result_for_pending(result)
                    
                elif result == XmrTxProofRequestResult.SUCCESS:
                    self.num_success_results += 1
                    if self.num_success_results < self.num_required_success_results:
                        # Request is success but not all have completed yet.
                        remaining = self.num_required_success_results - self.num_success_results
                        self.logger.info(f"{request} succeeded. We have {remaining} remaining request(s) open.")
                        asset_tx_proof_result = self.get_asset_tx_proof_result_for_pending(result)
                    else:
                        # All our services have returned a SUCCESS result so we
                        # have completed on the service level.
                        self.logger.info(
                            f"All {self.num_required_success_results} tx proof requests for trade "
                            f"{self.trade.get_short_id()} have been successful."
                        )
                        detail = result.detail
                        asset_tx_proof_result = (
                            AssetTxProofResult.COMPLETED.with_num_success_results(self.num_success_results)
                                        .with_num_required_success_results(self.num_required_success_results)
                                        .with_num_confirmations(detail.num_confirmations if detail else 0)
                                        .with_num_required_confirmations(self.auto_confirm_settings.required_confirmations)
                        )
                    
                elif result == XmrTxProofRequestResult.FAILED:
                    self.logger.warning(
                        f"{request} failed. This might not mean that the XMR transfer was invalid "
                        f"but you have to check yourself if the XMR transfer was correct. {result}"
                    )
                    asset_tx_proof_result = AssetTxProofResult.FAILED
                    
                else:  # ERROR or default
                    self.logger.warning(
                        f"{request} resulted in an error. This might not mean that the XMR transfer "
                        f"was invalid but can be a network or service problem. {result}"
                    )
                    asset_tx_proof_result = AssetTxProofResult.ERROR

                self.call_result_handler_and_maybe_terminate(result_handler, asset_tx_proof_result)

            request.request_from_service(handle_result, fault_handler)

    def was_terminated(self) -> bool:
        return not self.requests

    def add_settings_listener(self, result_handler: "Callable[[AssetTxProofResult], None]") -> None:
        def settings_callback() -> None:
            if not self.auto_confirm_settings.enabled:
                self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.FEATURE_DISABLED)
        
        self.auto_confirm_settings_listener = settings_callback
        self._subscriptions.append(self.auto_confirm_settings.add_listener(self.auto_confirm_settings_listener))

    def setup_trade_state_listener(self, result_handler: "Callable[[AssetTxProofResult], None]") -> None:
        def state_callback(change: SimplePropertyChangeEvent[TradeState]) -> None:
            if self.trade.is_payout_published:
                self.call_result_handler_and_maybe_terminate(
                    result_handler, AssetTxProofResult.PAYOUT_TX_ALREADY_PUBLISHED
                )
        
        self.trade_state_listener = state_callback
        self._subscriptions.append(self.trade.state_property.add_listener(self.trade_state_listener))

    def setup_arbitration_listener(
        self, result_handler: "Callable[[AssetTxProofResult], None]", refund_disputes: "ObservableList[Dispute]"
    ) -> None:
        def refund_callback(change: ObservableChangeEvent["Dispute"]) -> None:
            if change.added_elements and self.is_disputed(change.added_elements):
                self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.DISPUTE_OPENED)
        
        self.refund_listener = refund_callback
        self._subscriptions.append(refund_disputes.add_listener(self.refund_listener))

    def setup_mediation_listener(
        self, result_handler: "Callable[[AssetTxProofResult], None]", mediation_disputes: "ObservableList[Dispute]"
    ) -> None:
        def mediation_callback(change: ObservableChangeEvent["Dispute"]) -> None:
            if change.added_elements and self.is_disputed(change.added_elements):
                self.call_result_handler_and_maybe_terminate(result_handler, AssetTxProofResult.DISPUTE_OPENED)
        
        self.mediation_listener = mediation_callback
        self._subscriptions.append(mediation_disputes.add_listener(self.mediation_listener))

    def terminate(self) -> None:
        for request in self.requests:
            request.terminate()
        self.requests.clear()

        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

        if self.trade_state_listener is not None:
            self.trade.state_property.remove_listener(self.trade_state_listener)

        if self.auto_confirm_settings_listener is not None:
            self.auto_confirm_settings.remove_listener(self.auto_confirm_settings_listener)

        if self.mediation_listener is not None:
            self.mediation_manager.get_disputes_as_observable_list().remove_listener(self.mediation_listener)

        if self.refund_listener is not None:
            self.refund_manager.get_disputes_as_observable_list().remove_listener(self.refund_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def call_result_handler_and_maybe_terminate(
        self, result_handler: "Callable[[AssetTxProofResult], None]", asset_tx_proof_result: "AssetTxProofResult"
    ) -> None:
        result_handler(asset_tx_proof_result)
        if asset_tx_proof_result.is_terminal:
            self.terminate()

    def get_asset_tx_proof_result_for_pending(self, result: "XmrTxProofRequestResult") -> "AssetTxProofResult":
        detail = result.detail
        num_confirmations = detail.num_confirmations if detail else 0
        self.logger.info(f"{result} returned with num_confirmations {num_confirmations}")

        detail_string = ""
        if detail == XmrTxProofRequestDetail.PENDING_CONFIRMATIONS:
            detail_string = Res.get("portfolio.pending.autoConf.state.confirmations", num_confirmations, self.auto_confirm_settings.required_confirmations)
        elif detail == XmrTxProofRequestDetail.TX_NOT_FOUND:
            detail_string = Res.get("portfolio.pending.autoConf.state.txNotFound")

        return (
            AssetTxProofResult.PENDING.with_num_confirmations(self.num_success_results)
            .with_num_required_success_results(self.num_required_success_results)
            .with_num_confirmations(num_confirmations)
            .with_num_required_confirmations(self.auto_confirm_settings.required_confirmations)
            .with_details(detail_string)
        )
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Validation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_trade_amount_above_limit(self, trade: "Trade") -> bool:
        trade_amount = trade.get_amount()
        trade_limit = Coin.value_of(self.auto_confirm_settings.trade_limit)
        if trade_amount and trade_amount > trade_limit:
            self.logger.warning(
                f"Trade amount {trade_amount.to_friendly_string()} is higher than limit from auto-conf setting {trade_limit.to_friendly_string()}."
            )
            return True
        return False

    def is_disputed(self, disputes: list["Dispute"]) -> bool:
        return any(dispute.trade_id == self.trade.get_id() for dispute in disputes)
