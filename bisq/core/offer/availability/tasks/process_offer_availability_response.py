from bisq.common.setup.log_setup import get_logger
from bisq.common.taskrunner.task import Task
from bisq.common.taskrunner.task_runner import TaskRunner
from bisq.core.offer.availability.availability_result import AvailabilityResult
from bisq.core.offer.availability.dispute_agent_selection import DisputeAgentSelection
from bisq.core.offer.availability.messages.offer_availability_response import OfferAvailabilityResponse
from bisq.core.offer.availability.offer_availability_model import OfferAvailabilityModel
from bisq.core.offer.offer_state import OfferState

logger = get_logger(__name__)

class ProcessOfferAvailabilityResponse(Task[OfferAvailabilityModel]):
    
    def __init__(self, task_handler: TaskRunner[OfferAvailabilityModel], model: OfferAvailabilityModel):
        super().__init__(task_handler, model)

    def run(self):
        offer = self.model.offer
        try:
            self.run_intercept_hook()

            assert offer.state != OfferState.REMOVED, "Offer state must not be Offer.State.REMOVED"

            offer_availability_response = self.model.message

            if offer_availability_response.availability_result != AvailabilityResult.AVAILABLE:
                offer.state = OfferState.NOT_AVAILABLE
                self.failed(offer_availability_response.availability_result.description)
                return

            offer.state = OfferState.AVAILABLE

            self.model.selected_arbitrator = offer_availability_response.arbitrator

            mediator = offer_availability_response.mediator
            if mediator is None:
                # We do not get a mediator from old clients so we need to handle the null case.
                mediator = DisputeAgentSelection.get_random_mediator(self.model.mediator_manager).node_address
            self.model.selected_mediator = mediator

            self.model.selected_refund_agent = offer_availability_response.refund_agent

            self.complete()
        except Exception as e:
            offer.set_error_message(f"An error occurred.\nError message:\n{str(e)}")
            self.failed(e)


