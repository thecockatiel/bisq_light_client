from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.common.taskrunner.task_runner import TaskRunner
from bisq.core.offer.placeoffer.bisq_v1.tasks.add_to_offer_book import AddToOfferBook
from bisq.core.offer.placeoffer.bisq_v1.tasks.check_number_of_unconfirmed_transactions import (
    CheckNumberOfUnconfirmedTransactions,
)
from bisq.core.offer.placeoffer.bisq_v1.tasks.clone_address_entry_for_shared_maker_fee import (
    CloneAddressEntryForSharedMakerFee,
)
from bisq.core.offer.placeoffer.bisq_v1.tasks.create_maker_fee_tx import (
    CreateMakerFeeTx,
)
from bisq.core.offer.placeoffer.bisq_v1.tasks.validate_offer import ValidateOffer

if TYPE_CHECKING:
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.trade.bisq_v1.transaction_result_handler import (
        TransactionResultHandler,
    )
    from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel


class PlaceOfferProtocol:

    def __init__(
        self,
        model: "PlaceOfferModel",
        result_handler: "TransactionResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ) -> None:
        self.logger = get_ctx_logger(__name__)
        self.model = model
        self.result_handler = result_handler
        self.error_message_handler = error_message_handler

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Called from UI
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def place_offer(self):
        self.logger.debug(f"model.offer.id {self.model.offer.id}")

        def on_complete():
            self.logger.debug("sequence at handleRequestTakeOfferMessage completed")
            self.result_handler(self.model.transaction)

        def on_error(error_message: str):
            self.logger.error(error_message)

            if self.model.offer_added_to_offer_book:

                def handler():
                    self.model.offer_added_to_offer_book = False
                    self.logger.debug("OfferPayload removed from offer book.")

                self.model.offer_book_service.remove_offer(
                    self.model.offer.offer_payload_base, handler, self.logger.error
                )

            self.model.offer.error_message = error_message
            self.error_message_handler(error_message)

        task_runner = TaskRunner(
            self.model,
            on_complete,
            on_error,
        )

        if self.model.is_shared_maker_fee:
            task_runner.add_tasks(ValidateOffer, CloneAddressEntryForSharedMakerFee)
        else:
            task_runner.add_tasks(
                ValidateOffer,
                CheckNumberOfUnconfirmedTransactions,
                CreateMakerFeeTx,
                AddToOfferBook,
            )

        task_runner.run()
