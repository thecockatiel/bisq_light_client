from typing import TYPE_CHECKING
import grpc_pb2

if TYPE_CHECKING:
    from bisq.cli.grpc_stubs import GrpcStubs


class OffersServiceRequest:

    def __init__(self, grpc_stubs: "GrpcStubs"):
        self.grpc_stubs = grpc_stubs

    def get_available_offer_category(self, offer_id: str):
        return self._get_offer_category(offer_id, False)

    def get_my_offer_category(self, offer_id: str):
        return self._get_offer_category(offer_id, True)

    def create_bsq_swap_offer(
        self, direction: str, amount: int, min_amount: int, fixed_price: str
    ):
        request = grpc_pb2.CreateBsqSwapOfferRequest(
            direction=direction, amount=amount, min_amount=min_amount, price=fixed_price
        )
        response: grpc_pb2.CreateBsqSwapOfferReply = (
            self.grpc_stubs.offers_service.CreateBsqSwapOffer(request)
        )
        return response.bsq_swap_offer

    def create_fixed_priced_offer(
        self,
        direction: str,
        currency_code: str,
        amount: int,
        min_amount: int,
        fixed_price: str,
        security_deposit_pct: float,
        payment_acct_id: str,
        maker_fee_currency_code: str,
    ):
        return self.create_offer(
            direction=direction,
            currency_code=currency_code,
            amount=amount,
            min_amount=min_amount,
            use_market_based_price=False,
            fixed_price=fixed_price,
            market_price_margin_pct=0.00,
            security_deposit_pct=security_deposit_pct,
            payment_acct_id=payment_acct_id,
            maker_fee_currency_code=maker_fee_currency_code,
            trigger_price="0",  # no trigger price
        )

    def create_offer(
        self,
        direction: str,
        currency_code: str,
        amount: int,
        min_amount: int,
        use_market_based_price: bool,
        fixed_price: str,
        market_price_margin_pct: float,
        security_deposit_pct: float,
        payment_acct_id: str,
        maker_fee_currency_code: str,
        trigger_price: str,
    ):
        request = grpc_pb2.CreateOfferRequest(
            direction=direction,
            currency_code=currency_code,
            amount=amount,
            min_amount=min_amount,
            use_market_based_price=use_market_based_price,
            price=fixed_price,
            market_price_margin_pct=market_price_margin_pct,
            buyer_security_deposit_pct=security_deposit_pct,
            payment_account_id=payment_acct_id,
            maker_fee_currency_code=maker_fee_currency_code,
            trigger_price=trigger_price,
        )
        response: grpc_pb2.CreateOfferReply = (
            self.grpc_stubs.offers_service.CreateOffer(request)
        )
        return response.offer

    def edit_offer(
        self,
        offer_id: str,
        scaled_price_string: str,
        use_market_based_price: bool,
        market_price_margin_pct: float,
        trigger_price: str,
        enable: int,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ):
        # Take care when using this method directly:
        #  use_market_based_price = True if margin based offer, False for fixed priced offer
        #  scaled_price_string fmt = ######.####
        request = grpc_pb2.EditOfferRequest(
            id=offer_id,
            price=scaled_price_string,
            use_market_based_price=use_market_based_price,
            market_price_margin_pct=market_price_margin_pct,
            trigger_price=trigger_price,
            enable=enable,
            edit_type=edit_type,
        )
        response: grpc_pb2.EditOfferReply = self.grpc_stubs.offers_service.EditOffer(
            request
        )
        return response

    def cancel_offer(self, offer_id: str):
        request = grpc_pb2.CancelOfferRequest(id=offer_id)
        response: grpc_pb2.CancelOfferReply = (
            self.grpc_stubs.offers_service.CancelOffer(request)
        )
        return response

    def get_bsq_swap_offer(self, offer_id: str) -> "grpc_pb2.OfferInfo":
        request = grpc_pb2.GetOfferRequest(id=offer_id)
        response: grpc_pb2.GetBsqSwapOfferReply = (
            self.grpc_stubs.offers_service.GetBsqSwapOffer(request)
        )
        return response.bsq_swap_offer

    def get_offer(self, offer_id: str) -> "grpc_pb2.OfferInfo":
        request = grpc_pb2.GetOfferRequest(id=offer_id)
        response: grpc_pb2.GetOfferReply = self.grpc_stubs.offers_service.GetOffer(
            request
        )
        return response.offer

    def get_my_offer(self, offer_id: str) -> "grpc_pb2.OfferInfo":
        request = grpc_pb2.GetMyOfferRequest(id=offer_id)
        response: grpc_pb2.GetMyOfferReply = self.grpc_stubs.offers_service.GetMyOffer(
            request
        )
        return response.offer

    def get_bsq_swap_offers(self, direction: str) -> list["grpc_pb2.OfferInfo"]:
        request = grpc_pb2.GetBsqSwapOffersRequest(direction=direction)
        response: grpc_pb2.GetBsqSwapOffersReply = (
            self.grpc_stubs.offers_service.GetBsqSwapOffers(request)
        )
        return response.bsq_swap_offers

    def get_offers(
        self, direction: str, currency_code: str, all: bool
    ) -> list["grpc_pb2.OfferInfo"]:
        request = grpc_pb2.GetOffersRequest(
            direction=direction, currency_code=currency_code, all=all
        )
        response: grpc_pb2.GetOffersReply = self.grpc_stubs.offers_service.GetOffers(
            request
        )
        return response.offers

    def get_offers_sorted_by_date(
        self, currency_code: str, all: bool, direction: str = None
    ) -> list["grpc_pb2.OfferInfo"]:
        if direction is None:
            offers = []
            offers.extend(self.get_offers("BUY", currency_code, all))
            offers.extend(self.get_offers("SELL", currency_code, all))
            return offers if not offers else self.sort_offers_by_date(offers)
        else:
            offers = self.get_offers(direction, currency_code, all)
            return offers if not offers else self.sort_offers_by_date(offers)

    def get_bsq_swap_offers_sorted_by_date(self) -> list["grpc_pb2.OfferInfo"]:
        offers = []
        offers.extend(self.get_bsq_swap_offers("BUY"))
        offers.extend(self.get_bsq_swap_offers("SELL"))
        return self.sort_offers_by_date(offers)

    def get_my_offers_sorted_by_date(
        self, currency_code: str, direction: str = None
    ) -> list["grpc_pb2.OfferInfo"]:
        if direction is None:
            offers = []
            offers.extend(self.get_my_offers("BUY", currency_code))
            offers.extend(self.get_my_offers("SELL", currency_code))
            return offers if not offers else self.sort_offers_by_date(offers)
        else:
            offers = self.get_my_offers(direction, currency_code)
            return offers if not offers else self.sort_offers_by_date(offers)

    def get_my_offers(
        self, direction: str, currency_code: str
    ) -> list["grpc_pb2.OfferInfo"]:
        request = grpc_pb2.GetMyOffersRequest(
            direction=direction, currency_code=currency_code
        )
        response: grpc_pb2.GetMyOffersReply = (
            self.grpc_stubs.offers_service.GetMyOffers(request)
        )
        return response.offers

    def get_my_bsq_swap_offers_sorted_by_date(self) -> list["grpc_pb2.OfferInfo"]:
        offers = []
        offers.extend(self.get_my_bsq_swap_offers("BUY"))
        offers.extend(self.get_my_bsq_swap_offers("SELL"))
        return self.sort_offers_by_date(offers)

    def get_my_bsq_swap_offers(self, direction: str) -> list["grpc_pb2.OfferInfo"]:
        request = grpc_pb2.GetBsqSwapOffersRequest(direction=direction)
        response: grpc_pb2.GetBsqSwapOfferReply = (
            self.grpc_stubs.offers_service.GetMyBsqSwapOffers(request)
        )
        return response.bsq_swap_offer

    def sort_offers_by_date(self, offer_info_list: list["grpc_pb2.OfferInfo"]):
        return sorted(offer_info_list, key=lambda offer: offer.date)

    def _get_offer_category(self, offer_id: str, is_my_offer: bool):
        request = grpc_pb2.GetOfferCategoryRequest(id=offer_id, is_my_offer=is_my_offer)
        response: grpc_pb2.GetOfferCategoryReply = (
            self.grpc_stubs.offers_service.GetOfferCategory(request)
        )
        return response.offer_category
