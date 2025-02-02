import threading
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.model.offer_info import OfferInfo
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

logger = get_logger(__name__)


class GrpcOffersService(OffersServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def GetOfferCategory(
        self, request: "GetOfferCategoryRequest", context: "ServicerContext"
    ):
        try:
            return GetOfferCategoryReply(
                offer_category=self._get_offer_category(request.id, request.is_my_offer)
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def _get_offer_category(self, offer_id: str, is_my_offer: bool):
        if self.core_api.is_altcoin_offer(offer_id, is_my_offer):
            return GetOfferCategoryReply.OfferCategory.ALTCOIN
        elif self.core_api.is_fiat_offer(offer_id, is_my_offer):
            return GetOfferCategoryReply.OfferCategory.FIAT
        elif self.core_api.is_bsq_swap_offer(offer_id, is_my_offer):
            return GetOfferCategoryReply.OfferCategory.BSQ_SWAP
        else:
            return GetOfferCategoryReply.OfferCategory.UNKNOWN

    def GetBsqSwapOffer(self, request: "GetOfferRequest", context: "ServicerContext"):
        try:
            offer = self.core_api.get_offer(request.id)
            return GetBsqSwapOfferReply(
                bsq_swap_offer=OfferInfo.to_offer_info(offer).to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetOffer(self, request: "GetOfferRequest", context: "ServicerContext"):
        try:
            offer_id = request.id
            my_open_offer = self.core_api.find_my_open_offer(offer_id)
            offer = (
                my_open_offer.offer
                if my_open_offer
                else self.core_api.get_offer(offer_id)
            )
            offer_info = (
                OfferInfo.to_my_offer_info(my_open_offer)
                if my_open_offer
                else OfferInfo.to_offer_info(offer)
            )
            return GetOfferReply(offer=offer_info.to_proto_message())
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetMyBsqSwapOffer(
        self, request: "GetMyOfferRequest", context: "ServicerContext"
    ):
        try:
            offer = self.core_api.get_my_bsq_swap_offer(request.id)
            return GetMyBsqSwapOfferReply(
                bsq_swap_offer=OfferInfo.to_offer_info(
                    offer
                ).to_proto_message()  # JAVA TODO support triggerPrice
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    # Endpoint to be removed from future version.  Use getOffer service method instead.
    # Deprecated since 27-Dec-2021.
    def GetMyOffer(self, request: "GetMyOfferRequest", context: "ServicerContext"):
        try:
            logger.warning("GetMyOffer is deprecated. Use GetOffer instead.")
            offer = self.core_api.get_my_offer(request.id)
            return GetMyOfferReply(
                offer=OfferInfo.to_my_offer_info(offer).to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetBsqSwapOffers(
        self, request: "GetBsqSwapOffersRequest", context: "ServicerContext"
    ):
        try:
            offers = self.core_api.get_bsq_swap_offers(request.direction)
            return GetBsqSwapOffersReply(
                bsq_swap_offers=[
                    OfferInfo.to_offer_info(offer).to_proto_message()
                    for offer in offers
                ]
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetOffers(self, request: "GetOffersRequest", context: "ServicerContext"):
        try:
            offers = self.core_api.get_offers(
                request.direction, request.currency_code, request.all
            )
            offer_infos = [OfferInfo.to_offer_info(offer) for offer in offers]
            return GetOffersReply(
                offers=[offer_info.to_proto_message() for offer_info in offer_infos]
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetMyBsqSwapOffers(
        self, request: "GetBsqSwapOffersRequest", context: "ServicerContext"
    ):
        try:
            offers = self.core_api.get_my_bsq_swap_offers(request.direction)
            my_open_offers = [
                self.core_api.get_my_open_bsq_swap_offer(offer.id) for offer in offers
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
            self.exception_handler.handle_exception(logger, e, context)

    def GetMyOffers(self, request: "GetMyOffersRequest", context: "ServicerContext"):
        try:
            offers = self.core_api.get_my_offers(
                request.direction, request.currency_code
            )
            offer_infos = [OfferInfo.to_my_offer_info(offer) for offer in offers]
            return GetMyOffersReply(
                offers=[offer_info.to_proto_message() for offer_info in offer_infos]
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def CreateBsqSwapOffer(
        self, request: "CreateBsqSwapOfferRequest", context: "ServicerContext"
    ):
        # NOTE: this is only fine because grpc is running in a separate thread
        try:
            result_container = {"offer": None}
            completion_event = threading.Event()

            def callback(offer: "Offer"):
                result_container["offer"] = offer
                completion_event.set()

            self.core_api.create_and_place_bsq_swap_offer(
                request.direction,
                request.amount,
                request.min_amount,
                request.price,
                callback,
            )

            # NOTE: while it may be dangerous to wait indefinitely here, we should
            # thats because we want to know the result no matter what happens. either the offer is created or an error should be thrown
            completion_event.wait()

            offer = result_container["offer"]
            offer_info = OfferInfo.to_my_pending_offer_info(offer)
            return CreateBsqSwapOfferReply(bsq_swap_offer=offer_info.to_proto_message())
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def CreateOffer(self, request: "CreateOfferRequest", context: "ServicerContext"):
        try:
            result_container = {"offer": None}
            completion_event = threading.Event()

            def callback(offer: "Offer"):
                result_container["offer"] = offer
                completion_event.set()

            self.core_api.create_and_place_offer(
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
                callback,
            )

            # Wait for callback (indefinitely)
            completion_event.wait()

            offer = result_container["offer"]
            offer_info = OfferInfo.to_my_pending_offer_info(offer)
            return CreateOfferReply(offer=offer_info.to_proto_message())
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def EditOffer(self, request: "EditOfferRequest", context: "ServicerContext"):
        try:
            self.core_api.edit_offer(
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
            self.exception_handler.handle_exception(logger, e, context)

    def CancelOffer(self, request: "CancelOfferRequest", context: "ServicerContext"):
        try:
            self.core_api.cancel_offer(request.id)
            return CancelOfferReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)
