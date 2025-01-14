from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.taskrunner.task_runner import TaskRunner
from bisq.core.offer.placeoffer.bsq_swap.tasks.add_bsq_swap_offer_to_offer_book import (
    AddBsqSwapOfferToOfferBook,
)
from bisq.core.offer.placeoffer.bsq_swap.tasks.validate_bsq_swap_offer import (
    ValidateBsqSwapOffer,
)

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bsq_swap.place_bsq_swap_offer_model import (
        PlaceBsqSwapOfferModel,
    )


logger = get_logger(__name__)


class PlaceBsqSwapOfferProtocol:
    def __init__(
        self,
        model: "PlaceBsqSwapOfferModel",
        result_handler: Callable[[], None],
        error_message_handler: ErrorMessageHandler,
    ):
        self.model = model
        self.result_handler = result_handler
        self.error_message_handler = error_message_handler

    def place_offer(self):
        logger.debug(f"model.offer.id {self.model.offer.id}")

        def on_complete():
            logger.debug("sequence at handle_request_take_offer_message completed")
            self.result_handler()

        def on_error(error_message: str):
            logger.error(error_message)

            if self.model.offer_added_to_offer_book:

                def remove_complete():
                    self.model.offer_added_to_offer_book = False
                    logger.debug("OfferPayload removed from offer book.")

                self.model.offer_book_service.remove_offer(
                    self.model.offer.offer_payload_base,
                    remove_complete,
                    logger.error,
                )

            self.model.offer.error_message = error_message
            self.error_message_handler(error_message)

        task_runner = TaskRunner(self.model, on_complete, on_error)

        task_runner.add_tasks(ValidateBsqSwapOffer, AddBsqSwapOfferToOfferBook)

        task_runner.run()
