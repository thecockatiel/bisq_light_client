from typing import TYPE_CHECKING
from bisq.common.taskrunner.task import Task

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel
    from bisq.common.taskrunner.task_runner import TaskRunner


class AddToOfferBook(Task["PlaceOfferModel"]):
    def __init__(
        self, task_handler: "TaskRunner[PlaceOfferModel]", model: "PlaceOfferModel"
    ):
        super().__init__(task_handler, model)

    def run(self):
        try:
            self.run_intercept_hook()
            self.model.offer_book_service.add_offer(
                self.model.offer,
                self._on_success,
                self._on_error,
            )
        except Exception as e:
            self.model.offer.error_message = (
                f"An error occurred.\nError message:\n{str(e)}"
            )
            self.failed(exc=e)

    def _on_success(self):
        self.model.offer_added_to_offer_book = True
        self.complete()

    def _on_error(self, error_message: str):
        self.model.offer.error_message = (
            "Could not add offer to offerbook.\n"
            "Please check your network connection and try again."
        )
        self.failed(error_message)

