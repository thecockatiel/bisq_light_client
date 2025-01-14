from typing import TYPE_CHECKING
from bisq.common.taskrunner.task import Task

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bsq_swap.place_bsq_swap_offer_model import (
        PlaceBsqSwapOfferModel,
    )


class AddBsqSwapOfferToOfferBook(Task["PlaceBsqSwapOfferModel"]):

    def run(self):
        try:
            self.run_intercept_hook()

            def on_result():
                self.model.offer_added_to_offer_book = True
                self.complete()

            def on_error(msg: str):
                self.model.offer.error_message = (
                    "Could not add offer to offerbook.\n"
                    "Please check your network connection and try again."
                )
                self.failed(msg)

            self.model.offer_book_service.add_offer(
                self.model.offer,
                on_result,
                on_error,
            )
        except Exception as e:
            self.model.offer.error_message = f"An error occurred.\nError message:\n{e}"
            self.failed(exc=e)
