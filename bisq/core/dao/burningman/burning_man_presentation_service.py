from typing import TYPE_CHECKING
from bisq.core.dao.state.dao_state_listener import DaoStateListener

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.burningman.burning_man_service import BurningManService
    from bisq.core.dao.state.dao_state_service import DaoStateService

# TODO
class BurningManPresentationService(DaoStateListener):
    """Provides APIs for burningman data representation in the UI."""
    
    pass