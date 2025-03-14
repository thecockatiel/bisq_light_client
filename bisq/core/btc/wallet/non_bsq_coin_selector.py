from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.bisq_default_coin_selector import BisqDefaultCoinSelector
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey


if TYPE_CHECKING:
    from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list_service import (
        UnconfirmedBsqChangeOutputListService,
    )
    from bisq.core.user.preferences import Preferences
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction_output import TransactionOutput

logger = get_logger(__name__)


class NonBsqCoinSelector(BisqDefaultCoinSelector):
    """
    We use a specialized version of the CoinSelector based on the DefaultCoinSelector implementation.
    We lookup for spendable outputs which matches our address of our address.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        preferences: "Preferences",
    ):
        super().__init__(False)
        self._dao_state_service = dao_state_service
        self._preferences = preferences

    def is_tx_output_spendable(self, output: "TransactionOutput") -> bool:
        #  output.parent cannot be None as it is checked in calling method
        if output.parent is None:
            return False

        # It is important to not allow pending txs as otherwise unconfirmed BSQ txs would be considered nonBSQ as
        # below outputIsNotInBsqState would be true.
        if not output.parent.confirmations:
            return False

        key = TxOutputKey(output.parent.get_tx_id(), output.index)
        # It might be that we received BTC in a non-BSQ tx so that will not be stored in out state and not found.
        # So we consider any txOutput which is not in the state as BTC output.
        return not self._dao_state_service.exists_tx_output(
            key
        ) or self._dao_state_service.is_rejected_issuance_output(key)

    # Prevent usage of dust attack utxos
    def is_dust_attack_utxo(self, output: "TransactionOutput") -> bool:
        return output.value < self._preferences.get_ignore_dust_threshold()
