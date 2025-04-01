from datetime import timedelta
from typing import Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from utils.preconditions import check_argument
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.offer.offer import Offer
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.provider.mempool.fee_validation_status import FeeValidationStatus
from bisq.core.trade.model.tradable import Tradable
import pb_pb2 as protobuf

logger = get_logger(__name__)


class OpenOffer(Tradable):
    TIMEOUT_SEC = 60
    """Timeout for offer reservation during takeoffer process. If deposit tx is not completed in that time we reset the offer to AVAILABLE state."""

    def __init__(
        self,
        offer: "Offer",
        trigger_price: int = None,
        state: "OpenOfferState" = None,
        arbitrator_node_address: Optional["NodeAddress"] = None,
        mediator_node_address: Optional["NodeAddress"] = None,
        refund_agent_node_address: Optional["NodeAddress"] = None,
    ):
        if trigger_price is None:
            trigger_price = 0

        if state is None:
            state = OpenOfferState.AVAILABLE

        self.offer = offer
        self._state = state

        # JAVA TODO Not used. Could be removed?
        self.arbitrator_node_address = arbitrator_node_address
        self.mediator_node_address = mediator_node_address

        # Added v1.2.0
        self.refund_agent_node_address = refund_agent_node_address

        # Added in v1.5.3.
        # If market price reaches that trigger price the offer gets deactivated
        self.trigger_price = trigger_price

        self.fee_validation_status = FeeValidationStatus.NOT_CHECKED_YET  # transient
        self._timeout_timer: Optional["Timer"] = None  # transient

        # Added at BsqSwap release. We do not persist that field
        self.bsq_swap_offer_has_missing_funds = False  # transient

        if self.state == OpenOfferState.RESERVED:
            self.state = OpenOfferState.AVAILABLE

    def to_proto_message(self) -> "protobuf.Tradable":
        builder = protobuf.OpenOffer(
            offer=self.offer.to_proto_message(),
            trigger_price=self.trigger_price,
            state=OpenOfferState.to_proto_message(self.state),
        )

        if self.arbitrator_node_address:
            builder.arbitrator_node_address.CopyFrom(
                self.arbitrator_node_address.to_proto_message()
            )
        if self.mediator_node_address:
            builder.mediator_node_address.CopyFrom(
                self.mediator_node_address.to_proto_message()
            )
        if self.refund_agent_node_address:
            builder.refund_agent_node_address.CopyFrom(
                self.refund_agent_node_address.to_proto_message()
            )

        tradable = protobuf.Tradable(
            open_offer=builder,
        )
        return tradable

    @staticmethod
    def from_proto(proto: "protobuf.OpenOffer") -> "OpenOffer":
        return OpenOffer(
            offer=Offer.from_proto(proto.offer),
            state=OpenOfferState.from_proto(proto.state),
            arbitrator_node_address=(
                NodeAddress.from_proto(proto.arbitrator_node_address)
                if proto.HasField("arbitrator_node_address")
                else None
            ),
            mediator_node_address=(
                NodeAddress.from_proto(proto.mediator_node_address)
                if proto.HasField("mediator_node_address")
                else None
            ),
            refund_agent_node_address=(
                NodeAddress.from_proto(proto.refund_agent_node_address)
                if proto.HasField("refund_agent_node_address")
                else None
            ),
            trigger_price=proto.trigger_price,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Tradable
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_date(self):
        return self.offer.date

    def get_id(self):
        return self.offer.id

    def get_short_id(self):
        return self.offer.short_id

    def get_offer(self):
        return self.offer

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Misc
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state: "OpenOfferState"):
        self._state = new_state

        #  We keep it reserved for a limited time, if trade preparation fails we revert to available state
        if self._state == OpenOfferState.RESERVED:
            self.start_timeout()
        else:
            self.stop_timeout()

    @property
    def is_deactivated(self):
        return self.state == OpenOfferState.DEACTIVATED

    @property
    def is_canceled(self):
        return self.state == OpenOfferState.CANCELED

    @property
    def trigger_info_should_be_shown(self):
        return self.trigger_price > 0 or self.fee_validation_status.fails()

    def get_bsq_swap_offer_payload(self):
        check_argument(
            self.offer.bsq_swap_offer_payload is not None,
            "get_bsq_swap_offer_payload must be called only when BsqSwapOfferPayload is the expected payload"
        )
        return self.offer.bsq_swap_offer_payload

    def _on_timed_out(self):
        logger.debug("Timeout for resetting OpenOfferState.RESERVED reached")
        if self.state == OpenOfferState.RESERVED:
            # we do not need to persist that as at startup any RESERVED state would be reset to AVAILABLE anyway
            self.state = OpenOfferState.AVAILABLE

    def start_timeout(self):
        self.stop_timeout()

        UserThread.run_after(self._on_timed_out, timedelta(seconds=OpenOffer.TIMEOUT_SEC))

    def stop_timeout(self):
        if self._timeout_timer:
            self._timeout_timer.stop()
            self._timeout_timer = None

    def __str__(self):
        return (
            f"OpenOffer{{"
            f"\n     offer={self.offer},"
            f"\n     state={self.state},"
            f"\n     arbitratorNodeAddress={self.arbitrator_node_address},"
            f"\n     mediatorNodeAddress={self.mediator_node_address},"
            f"\n     refundAgentNodeAddress={self.refund_agent_node_address},"
            f"\n     triggerPrice={self.trigger_price},"
            f"\n     bsqSwapOfferHasMissingFunds={self.bsq_swap_offer_has_missing_funds}"
            "\n}}"
        )

    def __hash__(self):
        return hash(
            (
                self.trigger_price,
                self.offer,
                self.arbitrator_node_address,
                self.mediator_node_address,
                self.refund_agent_node_address,
            )
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, OpenOffer):
            return False
        return (
            self.trigger_price == other.trigger_price
            and self.offer == other.offer
            and self.arbitrator_node_address == other.arbitrator_node_address
            and self.mediator_node_address == other.mediator_node_address
            and self.refund_agent_node_address == other.refund_agent_node_address
        )
