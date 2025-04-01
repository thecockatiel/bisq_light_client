from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.locale.res import Res
from bitcoinj.core.reject_code import RejectCode
from utils.data import (
    SimpleProperty,
    SimplePropertyChangeEvent,
    combine_simple_properties,
)
from bisq.core.btc.exceptions.rejected_tx_exception import RejectedTxException

if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from bisq.core.api.core_context import CoreContext
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.trade.trade_manager import TradeManager

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
        self.wallet_service_error_msg_property = SimpleProperty("")
        self.btc_info_property = SimpleProperty(
            Res.get("mainView.footer.btcInfo.initializing")
        )
        self.rejected_tx_exception_property = SimpleProperty[
            Optional["RejectedTxException"]
        ](None)
        self.use_tor_for_btc_property = SimpleProperty(
            preferences.get_use_tor_for_bitcoin_j()
        )

    def init(
        self,
        chain_file_locked_exception_handler: Optional[Callable[[str], None]],
        spv_file_corrupted_handler: Optional[Callable[[str], None]],
        is_spv_resync_requested: bool,
        show_first_popup_if_resync_spv_requested_handler: Optional[Callable[[], None]],
        show_popup_if_invalid_btc_config_handler: Optional[Callable[[], None]],
        wallet_password_handler: Callable[[], None],
        download_complete_handler: Callable[[], None],
        wallet_initialized_handler: Callable[[], None],
    ):
        logger.info(f"Initialize WalletAppSetup with partial python port of BitcoinJ")

        wallet_service_exception = SimpleProperty[Exception]()

        def handle_btc_info(info: list):
            chain_height: int = info[0]
            # fee_update_counter: int = info[1]
            exception: Optional[Exception] = info[2]

            if not exception:
                if chain_height > 0:
                    synchronized_with = Res.get(
                        "mainView.footer.btcInfo.synchronizedWith",
                        self._get_btc_network_as_string(),
                        str(chain_height),
                    )
                    result = Res.get("mainView.footer.btcInfo", synchronized_with, info)
                    download_complete_handler()
                else:
                    result = Res.get(
                        "mainView.footer.btcInfo",
                        Res.get("mainView.footer.btcInfo.connectingTo"),
                        self._get_btc_network_as_string(),
                    )
            else:
                # TODO review later for correctness (I think branches never happen)
                result = Res.get(
                    "mainView.footer.btcInfo",
                    Res.get("mainView.footer.btcInfo.connectionFailed"),
                    self._get_btc_network_as_string(),
                )
                logger.error(exception)
                if isinstance(exception, TimeoutError):
                    self.wallet_service_error_msg_property.set(
                        Res.get("mainView.walletServiceErrorMsg.timeout")
                    )
                elif isinstance(exception, RejectedTxException):
                    self.rejected_tx_exception_property.set(exception)
                    self.wallet_service_error_msg_property.set(
                        Res.get(
                            "mainView.walletServiceErrorMsg.rejectedTxException",
                            str(exception),
                        )
                    )
                else:
                    self.wallet_service_error_msg_property.set(
                        Res.get(
                            "mainView.walletServiceErrorMsg.connectionError",
                            str(exception),
                        )
                    )
            return result

        self.btc_info_binding = combine_simple_properties(
            self.wallets_setup.chain_height_property,
            self.fee_service.fee_update_counter_property,
            wallet_service_exception,
            transform=handle_btc_info,
        )

        self.btc_info_binding.add_listener(
            lambda e: self.btc_info_property.set(e.new_value)
        )

        def on_initialized():
            # TODO handle wallet encryption later
            wallet_initialized_handler()

        def on_errored(e: Exception):
            wallet_service_exception.set(e)

        self.wallets_setup.initialize(None, on_initialized, on_errored)

    def set_rejected_tx_error_message_handler(
        self,
        rejected_tx_error_message_handler: Callable[[str], None],
        open_offer_manager: "OpenOfferManager",
        trade_manager: "TradeManager",
    ):
        def handler(e: SimplePropertyChangeEvent[Optional["RejectedTxException"]]):
            if e.new_value is None or e.new_value.tx_id is None:
                return

            reject_message = e.new_value.reject_message
            logger.warning(f"We received reject message: {reject_message}")

            # JAVA TODO: Find out which reject messages are critical and which not.
            # We got a report where a "tx already known" message caused a failed trade but the deposit tx was valid.
            # To avoid such false positives we only handle reject messages which we consider clearly critical.

            if reject_message.get_reason_code() in (
                RejectCode.OBSOLETE,
                RejectCode.DUPLICATE,
                RejectCode.NONSTANDARD,
                RejectCode.CHECKPOINT,
                RejectCode.OTHER,
            ):
                # We ignore those cases to avoid that not critical reject messages trigger a failed trade.
                logger.warning(
                    "We ignore that reject message as it is likely not critical."
                )

            elif reject_message.get_reason_code() in (
                RejectCode.MALFORMED,
                RejectCode.INVALID,
                RejectCode.DUST,
                RejectCode.INSUFFICIENTFEE,
            ):
                # We delay as we might get the rejected tx error before we have completed the create offer protocol
                logger.warning(
                    "We handle that reject message as it is likely critical."
                )
                tx_id = e.new_value.tx_id

                def process_delayed():

                    for open_offer in open_offer_manager.get_observable_list():
                        if tx_id == open_offer.get_offer().offer_fee_payment_tx_id:

                            def handle_offer():
                                open_offer.get_offer().error_message = (
                                    e.new_value.message
                                )
                                if rejected_tx_error_message_handler:
                                    rejected_tx_error_message_handler(
                                        Res.get(
                                            "popup.warning.openOffer.makerFeeTxRejected",
                                            open_offer.get_id(),
                                            tx_id,
                                        )
                                    )

                                def on_success():
                                    logger.warning(
                                        f"We removed an open offer because the maker fee was rejected by the Bitcoin "
                                        f"network. OfferId={open_offer.get_short_id()}, txId={tx_id}"
                                    )

                                open_offer_manager.remove_open_offer(
                                    open_offer, on_success, logger.warning
                                )

                            UserThread.run_after(handle_offer, timedelta(seconds=1))

                    # Handle trades
                    for trade in trade_manager.get_observable_list():
                        if trade.get_offer() is not None:
                            details = None
                            if tx_id == trade.deposit_tx_id:
                                details = Res.get(
                                    "popup.warning.trade.txRejected.deposit"
                                )
                            if (
                                tx_id == trade.get_offer().offer_fee_payment_tx_id
                                or tx_id == trade.taker_fee_tx_id
                            ):
                                details = Res.get(
                                    "popup.warning.trade.txRejected.tradeFee"
                                )

                            if details:

                                def handle_trade(trade_details=details):
                                    trade.error_message = e.new_value.message
                                    trade_manager.request_persistence()
                                    if rejected_tx_error_message_handler:
                                        rejected_tx_error_message_handler(
                                            Res.get(
                                                "popup.warning.trade.txRejected",
                                                trade_details,
                                                trade.get_short_id(),
                                                tx_id,
                                            )
                                        )

                                UserThread.run_after(handle_trade, timedelta(seconds=1))

                    UserThread.run_after(process_delayed, timedelta(seconds=3))

        self.rejected_tx_exception_property.add_listener(handler)

    def _get_btc_network_as_string(self) -> str:
        if self.config.ignore_local_btc_node:
            postfix = " " + Res.get("mainView.footer.localhostBitcoinNode")
        elif self.preferences.get_use_tor_for_bitcoin_j():
            postfix = " " + Res.get("mainView.footer.usingTor")
        else:
            postfix = ""
        return Res.get(self.config.base_currency_network.name) + postfix
