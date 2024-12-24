from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from bisq.common.taskrunner.task_model import TaskModel


if TYPE_CHECKING:
    from bisq.asset.coin import Coin
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.burningman.btc_fee_receiver_service import BtcFeeReceiverService
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.offer.offer import Offer
    from bisq.core.offer.offer_book_service import OfferBookService
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import ArbitratorManager
    from bisq.core.trade.statistics.trade_statistics_manager import TradeStatisticsManager
    from bisq.core.user.user import User
    from bitcoinj.core.transaction import Transaction 
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService


@dataclass
class PlaceOfferModel(TaskModel):
    # Immutable fields
    offer: 'Offer'
    reserved_funds_for_offer: 'Coin'
    use_savings_wallet: bool
    is_shared_maker_fee: bool
    wallet_service: 'BtcWalletService'
    trade_wallet_service: 'TradeWalletService'
    bsq_wallet_service: 'BsqWalletService'
    offer_book_service: 'OfferBookService'
    arbitrator_manager: 'ArbitratorManager'
    trade_statistics_manager: 'TradeStatisticsManager'
    dao_facade: 'DaoFacade'
    btc_fee_receiver_service: 'BtcFeeReceiverService'
    user: 'User'
    filter_manager: 'FilterManager'

    # Mutable fields
    offer_added_to_offer_book: bool = field(default=False, init=False)
    transaction: 'Transaction' = field(default=None, init=False)

    def on_complete(self):
        pass
