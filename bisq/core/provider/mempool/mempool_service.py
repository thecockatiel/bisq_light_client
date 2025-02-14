from asyncio import Future
import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Union

from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.provider.mempool.fee_validation_status import FeeValidationStatus
from bisq.core.provider.mempool.mempool_request import MempoolRequest
from bisq.core.provider.mempool.tx_validator import TxValidator
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
    from bisq.core.dao.burningman.burning_man_presentation_service import (
        BurningManPresentationService,
    )
    from bisq.common.config.config import Config
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.socks5_proxy_provider import Socks5ProxyProvider
    from bisq.core.user.preferences import Preferences

logger = get_logger(__name__)


# TODO
class MempoolService:
    def __init__(
        self,
        socks5_proxy_provider: "Socks5ProxyProvider",
        config: "Config",
        preferences: "Preferences",
        filter_manager: "FilterManager",
        dao_facade: "DaoFacade",
        dao_state_service: "DaoStateService",
        burning_man_presentation_service: "BurningManPresentationService",
    ):
        self.socks5_proxy_provider = socks5_proxy_provider
        self.config = config
        self.preferences = preferences
        self.filter_manager = filter_manager
        self.dao_facade = dao_facade
        self.dao_state_service = dao_state_service
        self.burning_man_presentation_service = burning_man_presentation_service
        self.outstanding_requests = 0

    def on_all_services_initialized(self):
        pass

    def request_tx_as_hex(self, tx_id: str) -> Future[str]:
        self.outstanding_requests += 1
        request = MempoolRequest(
            self.preferences, self.socks5_proxy_provider
        ).request_tx_as_hex(tx_id)

        def on_done(_):
            self.outstanding_requests -= 1

        request.add_done_callback(on_done)
        return request

    def can_request_be_made(self, offer_payload: "OfferPayload" = None) -> bool:
        can = (
            self.dao_state_service.parse_block_chain_complete
            and self.outstanding_requests < 5
        )  # limit max simultaneous lookups
        if offer_payload:
            #  when validating a new offer, wait 1 block for the tx to propagate
            can = (
                can
                and offer_payload.block_height_at_offer_creation
                < self.dao_state_service.chain_height
            )
        return can

    def validate_offer_maker_tx(
        self,
        input: Union["OfferPayload", "TxValidator"],
        result_handler: Callable[["TxValidator"], None],
    ):
        if isinstance(input, TxValidator):
            tx_validator = input
        else:
            # OfferPayload
            tx_validator = TxValidator(
                self.dao_state_service,
                input.offer_fee_payment_tx_id,
                self.filter_manager,
                Coin.value_of(input.amount),
                input.is_currency_for_maker_fee_btc,
                input.block_height_at_offer_creation,
            )

        if not self._is_service_supported():
            UserThread.run_after(
                lambda: result_handler(
                    tx_validator.end_result(FeeValidationStatus.ACK_CHECK_BYPASSED)
                ),
                timedelta(seconds=1),
            )
            return
        mempool_request = MempoolRequest(self.preferences, self.socks5_proxy_provider)
        self._do_validate_offer_maker_tx(mempool_request, tx_validator, result_handler)

    def _do_validate_offer_maker_tx(
        self,
        mempool_request: "MempoolRequest",
        tx_validator: "TxValidator",
        result_handler: Callable[["TxValidator"], None],
    ):
        future = asyncio.Future()

        future.add_done_callback(
            self._callback_for_maker_tx_validation(
                mempool_request, tx_validator, result_handler
            )
        )
        mempool_request.get_tx_status(future, tx_validator.tx_id)

    def _callback_for_maker_tx_validation(
        self,
        the_request: "MempoolRequest",
        tx_validator: "TxValidator",
        result_handler: Callable[["TxValidator"], None],
    ) -> Callable[["Future[str]"], None]:
        self.outstanding_requests += 1

        def on_success(json_txt: str):
            if tx_validator.is_fee_currency_btc:
                result_handler(
                    tx_validator.parse_json_validate_maker_fee_tx(
                        json_txt, self._get_all_btc_fee_receivers()
                    )
                )
            else:
                result_handler(tx_validator.validate_bsq_fee_tx(True))

        def on_failure():
            if the_request.switch_to_another_provider():
                self._do_validate_offer_maker_tx(
                    the_request, tx_validator, result_handler
                )
            else:
                # exhausted all providers, let user know of failure
                result_handler(
                    tx_validator.end_result(FeeValidationStatus.NACK_BTC_TX_NOT_FOUND)
                )

        def on_done(f: Future[str]):
            self.outstanding_requests -= 1
            try:
                json_txt = f.result()
                UserThread.execute(lambda: on_success(json_txt))
            except Exception as e:
                logger.warning(f"onFailure - {str(e)}")
                UserThread.execute(on_failure)

        return on_done

    def _get_all_btc_fee_receivers(self):
        btc_fee_receivers = list[str]()
        # fee receivers from filter ref: bisq-network/bisq/pull/4294
        filter = self.filter_manager.get_filter()
        if filter:
            fee_receivers = filter.btc_fee_receiver_addresses or []
        else:
            fee_receivers = []

        for receiver in fee_receivers:
            try:
                btc_fee_receivers.append(
                    receiver.split("#")[0]
                )  # victim's receiver address
            except:
                # If input format is not as expected we ignore entry
                pass
        btc_fee_receivers.extend(self.dao_facade.get_all_donation_addresses())

        # We use all BM who had ever had burned BSQ to avoid if a BM just got "deactivated" due decayed burn amounts
        # that it would trigger a failure here. There is still a small risk that new BM used for the trade fee payment
        # is not yet visible to the other peer, but that should be very unlikely.
        # We also get all addresses related to comp. requests, so this list is still rather long, but much shorter
        # than if we would use all addresses of all BM.
        bm_addresses = {
            address
            for candidate in self.burning_man_presentation_service.get_burning_man_candidates_by_name().values()
            if candidate.accumulated_burn_amount > 0
            for address in candidate.get_all_addresses()
        }
        btc_fee_receivers.extend(bm_addresses)

        return btc_fee_receivers

    def _is_service_supported(self):
        if (
            self.filter_manager.get_filter() is not None
            and self.filter_manager.get_filter().disable_mempool_validation
        ):
            logger.info(
                "MempoolService bypassed by filter setting disableMempoolValidation=true"
            )
            return False
        if self.config.bypass_mempool_validation:
            logger.info(
                "MempoolService bypassed by config setting bypassMempoolValidation=true"
            )
            return False
        if not self.config.base_currency_network.is_mainnet():
            logger.info("MempoolService only supports mainnet")
            return False
        if not self.can_request_be_made():
            logger.info("Tx Validation bypassed as service is not ready")
            return False
        return True
