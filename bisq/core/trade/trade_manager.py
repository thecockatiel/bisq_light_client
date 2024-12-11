from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.network.p2p.decrypted_direct_message_listener import (
    DecryptedDirectMessageListener,
)
from bisq.common.setup.log_setup import get_logger


if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import BsqSwapTradeManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.user.user import User

logger = get_logger(__name__)


# TODO
class TradeManager(PersistedDataHost, DecryptedDirectMessageListener):
    pass
