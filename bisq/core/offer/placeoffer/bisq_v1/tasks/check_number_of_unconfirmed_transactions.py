from typing import TYPE_CHECKING, List, Optional
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.locale.res import Res
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bisq.common.taskrunner.task import Task

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel
    from bisq.common.taskrunner.task_runner import TaskRunner


class CheckNumberOfUnconfirmedTransactions(Task["PlaceOfferModel"]):
    def __init__(
        self, task_handler: "TaskRunner[PlaceOfferModel]", model: "PlaceOfferModel"
    ):
        super().__init__(task_handler, model)

    def run(self):
        if (
            self.model.wallet_service.is_unconfirmed_transactions_limit_hit()
            or self.model.bsq_wallet_service.is_unconfirmed_transactions_limit_hit()
        ):
            return self.failed(Res.get("shared.unconfirmedTransactionsLimitReached"))
        self.complete()
