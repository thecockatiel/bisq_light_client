from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import logger_context
from bisq.common.util.utilities import WaitableResultHandler
from bisq.core.api.model.offer_info import OfferInfo
from bisq.core.user.user_context import UserContext
from grpc_pb2_grpc import OffersServicer
from grpc_pb2 import (
    CancelOfferReply,
    CancelOfferRequest,
    CreateBsqSwapOfferReply,
    CreateBsqSwapOfferRequest,
    CreateOfferReply,
    CreateOfferRequest,
    EditOfferReply,
    EditOfferRequest,
    GetBsqSwapOfferReply,
    GetBsqSwapOffersReply,
    GetBsqSwapOffersRequest,
    GetMyBsqSwapOfferReply,
    GetMyBsqSwapOffersReply,
    GetMyOfferReply,
    GetMyOfferRequest,
    GetMyOffersReply,
    GetMyOffersRequest,
    GetOfferCategoryRequest,
    GetOfferCategoryReply,
    GetOfferReply,
    GetOfferRequest,
    GetOffersReply,
    GetOffersRequest,
)

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi
    from bisq.core.user.user_manager import UserManager


class GrpcOffersService(OffersServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def GetOfferCategory(
        self, request: "GetOfferCategoryRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                return GetOfferCategoryReply(
                    offer_category=self._get_offer_category(
                        user_context,
                        request.id,
                        request.is_my_offer,
                    )
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def _get_offer_category(
        self, user_context: "UserContext", offer_id: str, is_my_offer: bool
    ):
        if self._core_api.is_altcoin_offer(user_context, offer_id, is_my_offer):
            return GetOfferCategoryReply.OfferCategory.ALTCOIN
        elif self._core_api.is_fiat_offer(user_context, offer_id, is_my_offer):
            return GetOfferCategoryReply.OfferCategory.FIAT
        elif self._core_api.is_bsq_swap_offer(user_context, offer_id, is_my_offer):
            return GetOfferCategoryReply.OfferCategory.BSQ_SWAP
        else:
            return GetOfferCategoryReply.OfferCategory.UNKNOWN

    def GetBsqSwapOffer(self, request: "GetOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offer = self._core_api.get_offer(user_context, request.id)
                return GetBsqSwapOfferReply(
                    bsq_swap_offer=OfferInfo.to_offer_info(offer).to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetOffer(self, request: "GetOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offer_id = request.id
                my_open_offer = self._core_api.find_my_open_offer(user_context, offer_id)
                offer = (
                    my_open_offer.offer
                    if my_open_offer
                    else self._core_api.get_offer(user_context, offer_id)
                )
                offer_info = (
                    OfferInfo.to_my_offer_info(my_open_offer)
                    if my_open_offer
                    else OfferInfo.to_offer_info(offer)
                )
                return GetOfferReply(offer=offer_info.to_proto_message())
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetMyBsqSwapOffer(
        self, request: "GetMyOfferRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offer = self._core_api.get_my_bsq_swap_offer(user_context, request.id)
                return GetMyBsqSwapOfferReply(
                    bsq_swap_offer=OfferInfo.to_offer_info(
                        offer
                    ).to_proto_message()  # JAVA TODO support triggerPrice
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    # Endpoint to be removed from future version.  Use getOffer service method instead.
    # Deprecated since 27-Dec-2021.
    def GetMyOffer(self, request: "GetMyOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                user_context.logger.warning(
                    "GetMyOffer is deprecated. Use GetOffer instead."
                )
                offer = self._core_api.get_my_offer(user_context, request.id)
                return GetMyOfferReply(
                    offer=OfferInfo.to_my_offer_info(offer).to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetBsqSwapOffers(
        self, request: "GetBsqSwapOffersRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offers = self._core_api.get_bsq_swap_offers(user_context, request.direction)
                return GetBsqSwapOffersReply(
                    bsq_swap_offers=[
                        OfferInfo.to_offer_info(offer).to_proto_message()
                        for offer in offers
                    ]
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetOffers(self, request: "GetOffersRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offers = self._core_api.get_offers(
                    user_context,
                    request.direction,
                    request.currency_code,
                )
                offer_infos = [OfferInfo.to_offer_info(offer) for offer in offers]
                return GetOffersReply(
                    offers=[offer_info.to_proto_message() for offer_info in offer_infos]
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetMyBsqSwapOffers(
        self, request: "GetBsqSwapOffersRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offers = self._core_api.get_my_bsq_swap_offers(
                    user_context, request.direction
                )
                my_open_offers = [
                    self._core_api.get_my_open_bsq_swap_offer(user_context, offer.id)
                    for offer in offers
                ]
                offer_infos = [
                    OfferInfo.to_my_offer_info(offer) for offer in my_open_offers
                ]
                return GetMyBsqSwapOffersReply(
                    bsq_swap_offers=[
                        offer_info.to_proto_message() for offer_info in offer_infos
                    ]
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetMyOffers(self, request: "GetMyOffersRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                offers = self._core_api.get_my_offers(
                    user_context,
                    request.direction,
                    request.currency_code,
                )
                offer_infos = [OfferInfo.to_my_offer_info(offer) for offer in offers]
                return GetMyOffersReply(
                    offers=[offer_info.to_proto_message() for offer_info in offer_infos]
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def CreateBsqSwapOffer(
        self, request: "CreateBsqSwapOfferRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                # NOTE: blocking is only fine because grpc is running in a separate thread
                waitable_handler = WaitableResultHandler["Offer"]()

                self._core_api.create_and_place_bsq_swap_offer(
                    user_context,
                    request.direction,
                    request.amount,
                    request.min_amount,
                    request.price,
                    waitable_handler,
                )

                # NOTE: while it may be dangerous to wait indefinitely here, we should
                # thats because we want to know the result no matter what happens. either the offer is created or an error should be thrown
                offer = waitable_handler.wait()
                offer_info = OfferInfo.to_my_pending_offer_info(offer)
                return CreateBsqSwapOfferReply(bsq_swap_offer=offer_info.to_proto_message())
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def CreateOffer(self, request: "CreateOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                waitable_handler = WaitableResultHandler["Offer"]()
                self._core_api.create_and_place_offer(
                    user_context,
                    request.currency_code,
                    request.direction,
                    request.price,
                    request.use_market_based_price,
                    request.market_price_margin_pct,
                    request.amount,
                    request.min_amount,
                    request.buyer_security_deposit_pct,
                    request.trigger_price,
                    request.payment_account_id,
                    request.maker_fee_currency_code,
                    waitable_handler,
                )

                # Wait for callback (indefinitely)
                offer = waitable_handler.wait()
                offer_info = OfferInfo.to_my_pending_offer_info(offer)
                return CreateOfferReply(offer=offer_info.to_proto_message())
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def EditOffer(self, request: "EditOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.edit_offer(
                    user_context,
                    request.id,
                    request.price,
                    request.use_market_based_price,
                    request.market_price_margin_pct,
                    request.trigger_price,
                    request.enable,
                    request.edit_type,
                )
                return EditOfferReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def CancelOffer(self, request: "CancelOfferRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.cancel_offer(user_context, request.id)
                return CancelOfferReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)
