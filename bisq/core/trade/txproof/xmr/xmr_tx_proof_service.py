from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, cast
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.trade.model.bisq_v1.seller_trade import SellerTrade
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.seller_protocol import SellerProtocol
from bisq.core.trade.txproof.asset_tx_proof_result import AssetTxProofResult
from bisq.core.trade.txproof.xmr.xmr_tx_proof_requests_per_trade import (
    XmrTxProofRequestsPerTrade,
)
from bisq.core.trade.txproof.asset_tx_proof_service import AssetTxProofService
from bisq.core.xmr.knaccc.monero.crypto.crypto_util import CryptoUtil
from utils.data import ObservableChangeEvent, SimpleProperty, SimplePropertyChangeEvent, combine_simple_properties

if TYPE_CHECKING:
    from bisq.core.user.auto_confirm_settings import AutoConfirmSettings
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.support.dispute.mediation.mediation_manager import MediationManager
    from bisq.core.support.refund.refund_manager import RefundManager
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.user.preferences import Preferences
    from bisq.core.filter.filter import Filter
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.trade.model.tradable import Tradable

logger = get_logger(__name__)

class XmrTxProofService(AssetTxProofService):
    """
    Entry point for clients to request tx proof and trigger auto-confirm if all conditions
    are met.
    """

    def __init__(
        self,
        filter_manager: "FilterManager",
        preferences: "Preferences",
        trade_manager: "TradeManager",
        closed_tradable_manager: "ClosedTradableManager",
        failed_trades_manager: "FailedTradesManager",
        mediation_manager: "MediationManager",
        refund_manager: "RefundManager",
        p2p_service: "P2PService",
        wallets_setup: "WalletsSetup",
        socks5_proxy_provider: "Socks5ProxyProvider",
    ):
        self.filter_manager = filter_manager
        self.preferences = preferences
        self.trade_manager = trade_manager
        self.closed_tradable_manager = closed_tradable_manager
        self.failed_trades_manager = failed_trades_manager
        self.mediation_manager = mediation_manager
        self.refund_manager = refund_manager
        self.p2p_service = p2p_service
        self.wallets_setup = wallets_setup
        self.socks5_proxy_provider = socks5_proxy_provider
        
        self.services_by_trade_id = dict[str, "XmrTxProofRequestsPerTrade"]()
        self.auto_confirm_settings: Optional["AutoConfirmSettings"]
        self.trade_state_listener_map = dict[str, Callable[[SimplePropertyChangeEvent[TradeState]], None]]()
        self.btc_peers_listener: Optional[Callable[[SimplePropertyChangeEvent[int]], None]] = None
        self.btc_block_listener: Optional[Callable[[SimplePropertyChangeEvent[int]], None]] = None
        self.bootstrap_listener: Optional["BootstrapListener"] = None
        self.p2p_network_and_wallet_ready: Optional[SimpleProperty[bool]] = None
        self.p2p_network_and_wallet_ready_listener: Optional[Callable[[SimplePropertyChangeEvent[bool]], None]] = None
        

    def on_all_services_initialized(self):
        # As we might trigger the payout tx we want to be sure that we are well connected to the Bitcoin network.
        # onAllServicesInitialized is called once we have received the initial data but we want to have our
        # hidden service published and upDatedDataResponse received before we start.
        is_p2p_bootsrapped = self.is_p2p_bootstrapped()
        has_sufficient_btc_peers = self.has_sufficient_btc_peers()
        is_btc_block_download_complete = self.is_btc_block_download_complete()
        if is_p2p_bootsrapped.get() and has_sufficient_btc_peers.get() and is_btc_block_download_complete.get():
            self.on_p2p_network_and_wallet_ready()
        else:
            self.p2p_network_and_wallet_ready = combine_simple_properties(is_p2p_bootsrapped, has_sufficient_btc_peers, is_btc_block_download_complete, transform=all)
            self.p2p_network_and_wallet_ready_listener = lambda e: self.on_p2p_network_and_wallet_ready() if e.new_value else None
            self.p2p_network_and_wallet_ready.add_listener(self.p2p_network_and_wallet_ready_listener)
            
    def shut_down(self):
        for service in self.services_by_trade_id.values():
            service.terminate()
        self.services_by_trade_id.clear()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_p2p_network_and_wallet_ready(self):
        if self.p2p_network_and_wallet_ready:
            self.p2p_network_and_wallet_ready.remove_listener(self.p2p_network_and_wallet_ready_listener)
            self.p2p_network_and_wallet_ready = None
            self.p2p_network_and_wallet_ready_listener = None
        
        auto_confirm_settings = self.preferences.find_auto_confirm_settings("XMR")
        if not auto_confirm_settings:
            logger.error("AutoConfirmSettings is not present")
            return
        
        # We register a listener to stop running services. For new trades we check anyway in the trade validation
        def on_filter_property_change(e: SimplePropertyChangeEvent["Filter"]):
            if self.is_auto_conf_disabled_by_filter():
                for service in self.services_by_trade_id.values():
                    trade = service.trade
                    trade.set_asset_tx_proof_result(
                        AssetTxProofResult.FEATURE_DISABLED.with_details(
                            Res.get("portfolio.pending.autoConf.state.filterDisabledFeature")
                        )
                    )
                self.trade_manager.request_persistence()
                self.shut_down()
        self.filter_manager.filter_property.add_listener(on_filter_property_change)
        
        # We listen on new trades
        tradable_list = self.trade_manager.tradable_list
        def on_trade_list_change(e: ObservableChangeEvent["Trade"]):
            if e.added_elements:
                self.process_trades(e.added_elements)
        tradable_list.add_listener(on_trade_list_change)
        
        # Process existing trades
        self.process_trades(tradable_list)

    def process_trades(self, trades: list["Tradable"]):
        for trade in trades:
            if isinstance(trade, SellerTrade) and \
                    self.is_xmr_trade(trade) and \
                    not trade.is_fiat_received: # Phase name is from the time when it was fiat only. Means counter currency (XMR) received.
                self.process_trade_or_add_listener(trade)
                
    # Basic requirements are fulfilled.
    # We process further if we are in the expected state or register a listener
    def process_trade_or_add_listener(self, trade: "SellerTrade"):
        if self.is_expected_trade_state(trade.get_trade_state()):
            self.start_requests_if_valid(trade)
        else:
            # We are expecting SELLER_RECEIVED_FIAT_PAYMENT_INITIATED_MSG in the future, so listen on changes
            def trade_state_listener(e: SimplePropertyChangeEvent["TradeState"]):
                if self.is_expected_trade_state(e.new_value):
                    listener = self.trade_state_listener_map.pop(trade.get_id(), None)
                    if listener:
                        trade.state_property.remove_listener(listener)
                    
                    self.start_requests_if_valid(trade)
                    
            self.trade_state_listener_map[trade.get_id()] = trade_state_listener
            trade.state_property.add_listener(trade_state_listener)
            
    def start_requests_if_valid(self, trade: "SellerTrade"):
        tx_hash = trade.counter_currency_tx_id
        tx_key = trade.counter_currency_extra_data
        
        if self.is_32_bit_hex_string_invalid(tx_hash) or self.is_32_bit_hex_string_invalid(tx_key):
            trade.set_asset_tx_proof_result(
                AssetTxProofResult.INVALID_DATA.with_details(Res.get("portfolio.pending.autoConf.state.txKeyOrTxIdInvalid"))
            )
            self.trade_manager.request_persistence()
            return
        
        canonical_tx_key = CryptoUtil.to_canoninal_tx_key(tx_key)
        if tx_key != canonical_tx_key:
            logger.error(f"Provided txKey is not in canonical form. txKey={tx_key}, canonicalTxKey={canonical_tx_key}")
            trade.set_asset_tx_proof_result(AssetTxProofResult.INVALID_DATA.with_details(Res.get("portfolio.pending.autoConf.state.txKeyOrTxIdInvalid")))
            self.trade_manager.request_persistence()
            return
        
        if self.is_auto_conf_disabled_by_filter():
            trade.set_asset_tx_proof_result(
                AssetTxProofResult.FEATURE_DISABLED.with_details(Res.get("portfolio.pending.autoConf.state.filterDisabledFeature"))
            )
            self.trade_manager.request_persistence()
            return

        if self.was_tx_key_re_used(trade, self.trade_manager.get_observable_list()):
            trade.set_asset_tx_proof_result(
                AssetTxProofResult.INVALID_DATA.with_details(Res.get("portfolio.pending.autoConf.state.xmr.txKeyReused"))
            )
            self.trade_manager.request_persistence()
            return

        self.start_requests(trade)
        
    def start_requests(self, trade: "SellerTrade"):
        service = XmrTxProofRequestsPerTrade(
            self.socks5_proxy_provider,
            self.auto_confirm_settings,
            trade,
            self.mediation_manager,
            self.filter_manager,
            self.refund_manager,
        )
        self.services_by_trade_id[trade.get_id()] = service
        
        def result_handler(asset_tx_proof_result: "AssetTxProofResult"):
            trade.set_asset_tx_proof_result(asset_tx_proof_result)
            
            if asset_tx_proof_result == AssetTxProofResult.COMPLETED:
                logger.info("###########################################################################################")
                logger.info(f"We auto-confirm trade {trade.get_short_id()} as our all our services for the tx proof completed successfully")
                logger.info("###########################################################################################")
                
                cast(SellerProtocol, self.trade_manager.get_trade_protocol()).on_payment_received(lambda: None, lambda e: None)
                
            if asset_tx_proof_result.is_terminal:
                self.services_by_trade_id.pop(trade.get_id(), None)
            
            self.trade_manager.request_persistence()
            
        def fault_handler(error_message: str, e: Exception):
            logger.error(error_message, exc_info=e)
            
        service.request_from_all_services(result_handler, fault_handler)
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Startup checks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_btc_block_download_complete(self) -> SimpleProperty[bool]:
        result = SimpleProperty(False)
        if self.wallets_setup.is_download_complete:
            result.set(True)
        else:
            def listener(e: SimplePropertyChangeEvent[int]):
                if self.wallets_setup.is_download_complete:
                    self.wallets_setup.chain_height_property.remove_listener(self.btc_block_listener)
                    result.set(True)
            self.btc_block_listener = listener
            self.wallets_setup.chain_height_property.add_listener(self.btc_block_listener)
        return result
    
    def has_sufficient_btc_peers(self) -> SimpleProperty[bool]:
        result = SimpleProperty(False)
        if self.wallets_setup.has_sufficient_peers_for_broadcast:
            result.set(True)
        else:
            def listener(e: SimplePropertyChangeEvent[int]):
                if self.wallets_setup.has_sufficient_peers_for_broadcast:
                    self.wallets_setup.num_peers_property.remove_listener(self.btc_peers_listener)
                    result.set(True)
            self.btc_peers_listener = listener
            self.wallets_setup.num_peers_property.add_listener(self.btc_peers_listener)
        return result
    
    def is_p2p_bootstrapped(self) -> SimpleProperty[bool]:
        result = SimpleProperty(False)
        if self.p2p_service.is_bootstrapped:
            result.set(True)
        else:
            class Listener(BootstrapListener):
                def on_data_received(self_):
                    self.p2p_service.remove_p2p_service_listener(self.bootstrap_listener)
                    result.set(True)
            self.bootstrap_listener = Listener()
            self.p2p_service.add_p2p_service_listener(self.bootstrap_listener)
        return result
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Validation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_xmr_trade(self, trade: "Trade") -> bool:
        assert trade.get_offer() is not None
        return trade.get_offer().currency_code == "XMR"
    
    def is_expected_trade_state(self, trade_state: "TradeState") -> bool:
        return trade_state == TradeState.SELLER_RECEIVED_FIAT_PAYMENT_INITIATED_MSG
    
    def is_32_bit_hex_string_invalid(self, hex_string: Optional[str]) -> bool:
        if not hex_string or not hex_string.isalnum() or len(hex_string) != 64:
            logger.warning(f"Invalid hexString: {hex_string}")
            return True
        return False

    def is_auto_conf_disabled_by_filter(self) -> bool:
        filter = self.filter_manager.filter_property.value
        return filter is not None and filter.disable_auto_conf
    
    def was_tx_key_re_used(self, trade: "Trade", active_trades: list["Trade"]) -> bool:
        # For dev testing we reuse test data, so we ignore that check
        if DevEnv.is_dev_mode():
            return False

        # We need to prevent that a user tries to scam by reusing a txKey and txHash of a previous XMR trade with
        # the same user (same address) and same amount.
        # We check additionally to the txKey also the txHash though different
        # txKey is not possible to get a valid result at proof.
        failed_and_open_trades = active_trades + self.failed_trades_manager.get_observable_list()
        closed_trades = [t for t in self.closed_tradable_manager.get_observable_list() if isinstance(t, Trade)]
        all_trades = failed_and_open_trades + closed_trades
        trade_tx_key = trade.counter_currency_extra_data
        trade_tx_hash = trade.counter_currency_tx_id

        for t in all_trades:
            if t.get_id() == trade.get_id():
                continue
            tx_key = t.counter_currency_extra_data
            tx_hash = t.counter_currency_tx_id
            if not tx_key or not tx_hash:
                continue

            if tx_key.lower() == trade_tx_key.lower():
                logger.warning(f"Peer used the XMR tx key already at another trade with trade ID {t.get_id()}. This might be a scam attempt.")
                return True
            if tx_hash.lower() == trade_tx_hash.lower():
                logger.warning(f"Peer used the XMR tx ID already at another trade with trade ID {t.get_id()}. This might be a scam attempt.")
                return True

        return False
