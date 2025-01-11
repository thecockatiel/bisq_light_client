from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.res import Res
from utils.data import SimpleProperty, combine_simple_properties

if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from bisq.core.api.core_context import CoreContext
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences

logger = get_logger(__name__)

# TODO
class WalletAppSetup:

    def __init__(
        self,
        core_context: "CoreContext",
        wallets_manager: "WalletsManager",
        wallets_setup: "WalletsSetup",
        fee_service: "FeeService",
        config: "Config",
        preferences: "Preferences",
    ):
        self.core_context = core_context
        self.wallets_manager = wallets_manager
        self.wallets_setup = wallets_setup
        self.fee_service = fee_service
        self.config = config
        self.preferences = preferences

        self.btc_info_binding: Optional[SimpleProperty[str]] = None
        self.btc_sync_progress_property = SimpleProperty(-1.0)
        self.wallet_service_error_msg_propery = SimpleProperty("")
        self.btc_splash_sync_icon_id_property = SimpleProperty("")
        self.btc_info_property = SimpleProperty(Res.get("mainView.footer.btcInfo.initializing"))
        self.rejected_tx_exception_property = SimpleProperty(None)
        self.use_tor_for_btc_property = SimpleProperty(preferences.get_use_tor_for_bitcoin_j())
        
    def init(
        self,
        chain_file_locked_exception_handler: Optional[Callable[[str], None]],
        spv_file_corrupted_handler: Optional[Callable[[str], None]],
        is_spv_resync_requested: bool,
        show_first_popup_if_resync_spv_requested_handler: Optional[Callable[[], None]],
        show_popup_if_invalid_btc_config_handler: Optional[Callable[[], None]],
        wallet_password_handler: Callable[[], None],
        download_complete_handler: Callable[[], None],
        wallet_initialized_handler: Callable[[], None]
    ):
        logger.info(f"Initialize WalletAppSetup with partial python port of BitcoinJ")
        
        # wallet_service_exception = SimpleProperty[Exception]()
        
        # def handle_btc_info(info: list[Union[Literal['UNSET'], Any]]):
        #     download_percentage: float = info[0]
        #     chain_height: int = info[1]
        #     fee_update_counter: int = info[2]
        #     exception: Optional[Exception] = info[3]
        #     result = None
        
        # self.btc_info_binding = combine_simple_properties(
        #     self.wallets_setup.download_percentage_property,
        #     self.wallets_setup.chain_height_property,
        #     self.fee_service.fee_update_counter_property,
        #     wallet_service_exception,
        #     transform=handle_btc_info
        # ) 
