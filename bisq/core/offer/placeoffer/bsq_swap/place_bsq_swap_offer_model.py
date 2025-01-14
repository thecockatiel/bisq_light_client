from typing import TYPE_CHECKING
from bisq.common.taskrunner.task_model import TaskModel

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.offer.offer_book_service import OfferBookService


class PlaceBsqSwapOfferModel(TaskModel):
    def __init__(self, offer: "Offer", offer_book_service: "OfferBookService"):
        self.offer = offer
        self.offer_book_service = offer_book_service
        self.offer_added_to_offer_book = False

    def on_complete(self):
        pass
