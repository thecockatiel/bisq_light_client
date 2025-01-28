from decimal import Decimal
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.offer.open_offer import OpenOffer

logger = get_logger(__name__)

DECIMAL_ZERO = Decimal("0")


class EditOfferValidator:

    @staticmethod
    def is_editing_use_mkt_price_margin_flag(
        offer: "Offer", edit_type: grpc_pb2.EditOfferRequest.EditType
    ) -> bool:
        if edit_type == grpc_pb2.EditOfferRequest.EditType.ACTIVATION_STATE_ONLY:
            # If only changing activation state, we are not editing offer.isUseMarketBasedPrice flag.
            return offer.is_use_market_based_price
        else:
            return (
                edit_type == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_ONLY
                or edit_type
                == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_ACTIVATION_STATE
                or edit_type == grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_ONLY
                or edit_type
                == grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_AND_ACTIVATION_STATE
                or edit_type
                == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE
                or edit_type
                == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE_AND_ACTIVATION_STATE
            )

    @staticmethod
    def is_editing_mkt_price_margin(
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ) -> bool:
        return (
            edit_type == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_ONLY
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_ACTIVATION_STATE
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE_AND_ACTIVATION_STATE
        )

    @staticmethod
    def is_editing_trigger_price(edit_type: grpc_pb2.EditOfferRequest.EditType) -> bool:
        return (
            edit_type == grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_ONLY
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_AND_ACTIVATION_STATE
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE_AND_ACTIVATION_STATE
        )

    @staticmethod
    def is_editing_fixed_price(edit_type: grpc_pb2.EditOfferRequest.EditType) -> bool:
        return (
            edit_type == grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_ONLY
            or edit_type
            == grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_AND_ACTIVATION_STATE
        )

    def __init__(
        self,
        currently_open_offer: "OpenOffer",
        new_price: str,
        new_is_use_market_based_price: bool,
        new_market_price_margin: float,
        new_trigger_price: str,
        new_enable: int,
        edit_type: grpc_pb2.EditOfferRequest.EditType,
    ):
        self.currently_open_offer = currently_open_offer
        self.new_price = "0" if not new_price.strip() else new_price
        # TODO: check the comment below and make the change ?
        # The client cannot determine what offer.isUseMarketBasedPrice should be
        # when editType = ACTIVATION_STATE_ONLY.  Override newIsUseMarketBasedPrice
        # param for the ACTIVATION_STATE_ONLY case.
        # A cleaner solution might be possible if the client fetched the offer
        # before sending an edit request, but that's an extra round trip to the server.
        self.new_is_use_market_based_price = (
            currently_open_offer.get_offer().is_use_market_based_price
            if edit_type == grpc_pb2.EditOfferRequest.EditType.ACTIVATION_STATE_ONLY
            else new_is_use_market_based_price
        )
        self.new_market_price_margin = new_market_price_margin
        self.new_trigger_price = (
            "0" if not new_trigger_price.strip() else new_trigger_price
        )
        self.new_enable = new_enable
        self.edit_type = edit_type

        self.is_zero_edited_fixed_price_string = Decimal(self.new_price).is_zero()
        self.is_zero_edited_trigger_price = Decimal(self.new_trigger_price).is_zero()

    def validate(self) -> "EditOfferValidator":
        logger.info(f"Verifying 'editoffer' params for editType {self.edit_type}")
        self._check_not_bsq_swap_offer()

        if self.edit_type == grpc_pb2.EditOfferRequest.EditType.ACTIVATION_STATE_ONLY:
            self._validate_edited_activation_state()
        elif self.is_editing_fixed_price(self.edit_type):
            self._validate_edited_fixed_price()
        elif self.is_editing_mkt_price_margin(
            self.edit_type
        ) or self.is_editing_trigger_price(self.edit_type):
            self._check_not_bsq_offer()
            self._validate_edited_trigger_price()
            self._validate_edited_market_price_margin()

        return self

    def __str__(self):
        is_editing_mkt_price_margin = self.is_editing_mkt_price_margin(self.edit_type)
        is_editing_price = self.is_editing_fixed_price(self.edit_type)
        offer = self.currently_open_offer.get_offer()

        return (
            f"EditOfferValidator{{\n"
            f"  offer={offer.id}\n"
            f"  offer.payloadBase.price={offer.offer_payload_base.price}\n"
            f"  newPrice={self.new_price if is_editing_price else 'N/A'}\n"
            f"  offer.useMarketBasedPrice={offer.is_use_market_based_price}\n"
            f"  newUseMarketBasedPrice={self.new_is_use_market_based_price}\n"
            f"  offer.marketPriceMargin={offer.market_price_margin}\n"
            f"  newMarketPriceMargin={self.new_market_price_margin if is_editing_mkt_price_margin else 'N/A'}\n"
            f"  offer.triggerPrice={self.currently_open_offer.trigger_price}\n"
            f"  newTriggerPrice={self.new_trigger_price if self.is_editing_trigger_price(self.edit_type) else 'N/A'}\n"
            f"  newEnable={self.new_enable}\n"
            f"  editType={self.edit_type}\n"
            f"}}"
        )

    def _validate_edited_activation_state(self):
        if self.new_enable < 0:
            raise IllegalStateException(
                f"programmer error: the 'enable' request parameter does not"
                f" indicate activation state of offer with id '{self.currently_open_offer.get_id()}' should be changed."
            )

        enable_description = "deactivate" if self.new_enable == 0 else "activate"
        pricing_description = (
            "mkt price margin"
            if self.currently_open_offer.get_offer().is_use_market_based_price
            else "fixed price"
        )
        logger.info(
            f"Attempting to {enable_description} {pricing_description} offer with id '{self.currently_open_offer.get_id()}'."
        )

    def _validate_edited_fixed_price(self):
        if self.currently_open_offer.get_offer().is_use_market_based_price:
            logger.info(
                f"Attempting to change mkt price margin based offer with id '{self.currently_open_offer.get_id()}' to fixed price offer."
            )

        if self.new_is_use_market_based_price:
            raise IllegalStateException(
                f"programmer error: cannot change fixed price ({self.new_market_price_margin})"
                f" in mkt price based offer with id '{self.currently_open_offer.get_id()}'"
            )

        if not self.is_zero_edited_trigger_price:
            raise IllegalStateException(
                f"programmer error: cannot change trigger price ({self.new_trigger_price})"
                f" in offer with id '{self.currently_open_offer.get_id()}' when changing fixed price"
            )

    def _validate_edited_market_price_margin(self):
        if not self.currently_open_offer.get_offer().is_use_market_based_price:
            logger.info(
                f"Attempting to change fixed price offer with id '{self.currently_open_offer.get_id()}' to mkt price margin based offer."
            )

        if not self.is_zero_edited_fixed_price_string:
            raise IllegalStateException(
                f"programmer error: cannot set fixed price ({self.new_price})"
                f" in mkt price margin based offer with id '{self.currently_open_offer.get_id()}'"
            )

    def _validate_edited_trigger_price(self):
        if (
            not self.currently_open_offer.get_offer().is_use_market_based_price
            and not self.new_is_use_market_based_price
            and not self.is_zero_edited_trigger_price
        ):
            raise IllegalStateException(
                f"programmer error: cannot set a trigger price"
                f" in fixed price offer with id '{self.currently_open_offer.get_id()}'"
            )

        if Decimal(self.new_trigger_price) < DECIMAL_ZERO:
            raise IllegalStateException(
                f"programmer error: cannot set trigger price to a negative value"
                f" in offer with id '{self.currently_open_offer.get_id()}'"
            )

    def _check_not_bsq_offer(self):
        if self.currently_open_offer.get_offer().currency_code == "BSQ":
            # is a user error.
            raise ValueError(
                f"cannot set mkt price margin or trigger price on fixed price bsq offer with id '{self.currently_open_offer.get_id()}'"
            )

    def _check_not_bsq_swap_offer(self):
        if self.currently_open_offer.get_offer().is_bsq_swap_offer:
            # is a user error.
            raise ValueError(
                f"cannot edit bsq swap offer with id '{self.currently_open_offer.get_id()}', replace it with a new swap offer instead"
            )
