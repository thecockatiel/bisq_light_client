from typing import TYPE_CHECKING, Optional
from collections.abc import Callable
from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from bisq.core.network.p2p.network.close_connection_reason import CloseConnectionReason
from bisq.core.network.p2p.network.connection_listener import ConnectionListener
from bisq.core.network.p2p.p2p_service_listener import P2PServiceListener
from bisq.core.network.p2p.storage.payload.proof_of_work_payload import ProofOfWorkPayload
from bisq.core.provider.price.price_feed_service import PriceFeedService
from utils.data import SimpleProperty, combine_simple_properties

if TYPE_CHECKING:
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.network.connection import Connection
    
logger = get_logger(__name__)

# NOTE: we do not need Preferences here, so they are omitted in python implementation
# TODO: WalletsSetup needs to be checked and implemented accordingly later if needed
# TODO: Heavily tied to UI, need to investigate on how to make it UI agnostic.

class P2PNetworkSetup:
    def __init__(self, price_feed_service: "PriceFeedService", p2p_service: "P2PService", filter_manager: "FilterManager"):
        self.price_feed_service = price_feed_service
        self.p2p_service = p2p_service
        self.filter_manager = filter_manager

        
        self.p2p_network_info = SimpleProperty("")
        self.p2p_network_icon_id = SimpleProperty("")
        self.p2p_network_status_icon_id = SimpleProperty("")
        self.splash_p2p_network_animation_visible = SimpleProperty(True)
        self.p2p_network_label_id = SimpleProperty("footer-pane")
        self.p2p_network_warn_msg = SimpleProperty("")
        self.data_received = SimpleProperty(False)
        self.p2p_network_failed = SimpleProperty(False)
 
        self.p2p_network_info_binding: Optional[SimpleProperty[str]]
        
    def init(self, init_wallet_service_handler: Callable, display_tor_network_settings_handler: Callable[[bool], None]) -> SimpleProperty[bool]:
        bootstrap_state = SimpleProperty[Optional[str]](None)
        bootstrap_warning = SimpleProperty[Optional[str]](None)
        hidden_service_published = SimpleProperty(False)
        
        self.add_p2p_message_filter()
        
        def handle_network_binding(*args):
            state: str = args[0]
            warning: str = args[1]
            num_p2p_peers: int = args[2]
            hidden_service: bool = args[3]
            data_received: bool = args[4]
            result = ""
            
            if warning is not None and num_p2p_peers == 0:
                result = warning
            else:
                p2pinfo = Res.get("mainView.footer.p2pInfo", num_p2p_peers) # NOTE: no btc node handling in python implementation
                if data_received and hidden_service:
                    result = p2pinfo
                elif num_p2p_peers == 0:
                    result = state
                else:
                    result = state + " / " + p2pinfo
            return result
                    
            
            
        self.p2p_network_info_binding = combine_simple_properties(bootstrap_state, bootstrap_warning, self.p2p_service.get_num_connected_peers(), hidden_service_published, self.data_received, transform=handle_network_binding)
        self.p2p_network_info_binding.add_listener(lambda e: self.p2p_network_info.set(e.new_value))\
            
        bootstrap_state.set(Res.get("mainView.bootstrapState.connectionToTorNetwork"))
        
        outer = self
        
        class CListener(ConnectionListener):
            def on_connection(self, connection: "Connection"):
                return outer.update_network_status_indicator()
            
            def on_disconnect(self, close_connection_reason: "CloseConnectionReason", connection: "Connection"):
                outer.update_network_status_indicator()
                # We only check at seed nodes as they are running the latest version
                # Other disconnects might be caused by peers running an older version
                if connection.connection_state.is_seed_node and close_connection_reason == CloseConnectionReason.RULE_VIOLATION:
                    logger.warning(f"RULE_VIOLATION onDisconnect closeConnectionReason={close_connection_reason}, connection={connection}")
        
        self.p2p_service.get_network_node().add_connection_listener(CListener())
        
        p2p_network_initialized = SimpleProperty(False)
        
        class P2pSvcListener(P2PServiceListener):
            def on_tor_node_ready(self) -> None:
                logger.debug("on_tor_node_ready")
                bootstrap_state.set(Res.get("mainView.bootstrapState.torNodeCreated"))
                outer.p2p_network_icon_id.set("image-connection-tor")
                
                # init_wallet_service_handler was used here with preferences
                
                # We want to get early connected to the price relay so we call it already now
                outer.price_feed_service.set_currency_code_on_init()
                outer.price_feed_service.initial_request_price_feed()
                
            def on_hidden_service_published(self) -> None:
                logger.debug("on_hidden_service_published")
                hidden_service_published.set(True)
                bootstrap_state.set(Res.get("mainView.bootstrapState.hiddenServicePublished"))
                
            def on_data_received(self):
                logger.debug("on_data_received")
                bootstrap_state.set(Res.get("mainView.bootstrapState.initialDataReceived"))
                outer.data_received.set(True)
                outer.splash_p2p_network_animation_visible.set(False)
                p2p_network_initialized.set(True)
                
            def on_no_seed_node_available(self):
                logger.warning("on_no_seed_node_available")
                if outer.p2p_service.get_num_connected_peers().get() == 0:
                    bootstrap_warning.set(Res.get("mainView.bootstrapWarning.noSeedNodesAvailable"))
                else:
                    bootstrap_warning.set(None)
                    
                outer.splash_p2p_network_animation_visible.set(False)
                p2p_network_initialized.set(True)
            
            def on_no_peers_available(self):
                logger.warning("on_no_peers_available")
                if outer.p2p_service.get_num_connected_peers().get() == 0:
                    outer.p2p_network_warn_msg.set(Res.get("mainView.p2pNetworkWarnMsg.noNodesAvailable"))
                    bootstrap_warning.set(Res.get("mainView.bootstrapWarning.noNodesAvailable"))
                    outer.p2p_network_label_id.set("splash-error-state-msg")
                else:
                    bootstrap_warning.set(None)
                    outer.p2p_network_label_id.set("footer-pane")
                outer.splash_p2p_network_animation_visible.set(False)
                p2p_network_initialized.set(True)
                
            def on_updated_data_received(self):
                logger.debug("on_updated_data_received")
                outer.splash_p2p_network_animation_visible.set(False)
                
            def on_setup_failed(self, e: Exception | None = None) -> None:
                logger.error("on_setup_failed")
                outer.p2p_network_warn_msg.set(Res.get("mainView.p2pNetworkWarnMsg.connectionToP2PFailed", str(e)))
                outer.splash_p2p_network_animation_visible.set(False)
                bootstrap_warning.set(Res.get("mainView.bootstrapWarning.bootstrappingToP2PFailed"))
                outer.p2p_network_label_id.set("splash-error-state-msg")
                outer.p2p_network_failed.set(True)
                
            def on_request_custom_bridges(self) -> None:
                if display_tor_network_settings_handler is not None:
                    display_tor_network_settings_handler(True)
        
        self.p2p_service.start(P2pSvcListener())
        
        return p2p_network_initialized
    
    def add_p2p_message_filter(self):
        def predicate(payload):
            filter = self.filter_manager.get_filter()
            return filter is None or not filter.disable_pow_message or not isinstance(payload, ProofOfWorkPayload)
            
        self.p2p_service.p2p_data_storage.filter_predicate = predicate
        
    def update_network_status_indicator(self):
        if self.p2p_service.network_node.get_inbound_connection_count() > 0:
            self.p2p_network_status_icon_id.set("image-green_circle")
        elif self.p2p_service.network_node.get_outbound_connection_count() > 0:
            self.p2p_network_status_icon_id.set("image-yellow_circle")
        else:
            self.p2p_network_status_icon_id.set("image-alert-round")