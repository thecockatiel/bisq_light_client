from typing import TYPE_CHECKING

from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.bisq_default_coin_selector import BisqDefaultCoinSelector
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey


if TYPE_CHECKING:
    from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list_service import (
        UnconfirmedBsqChangeOutputListService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bitcoinj.core.transaction_output import TransactionOutput

logger = get_logger(__name__)


class BsqCoinSelector(BisqDefaultCoinSelector):
    """
    We use a specialized version of the CoinSelector based on the DefaultCoinSelector implementation.
    We lookup for spendable outputs which matches any of our addresses.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        unconfirmed_bsq_change_output_list_service: "UnconfirmedBsqChangeOutputListService",
    ):
        # permitForeignPendingTx is not relevant here as we do not support pending foreign utxos anyway.
        super().__init__(False)
        self._dao_state_service = dao_state_service
        self._unconfirmed_bsq_change_output_list_service = (
            unconfirmed_bsq_change_output_list_service
        )
        self.allow_spend_my_own_unconfirmed_tx_outputs = True

    def is_tx_output_spendable(self, output: "TransactionOutput") -> bool:
        parent_transaction = output.parent
        if parent_transaction is None:
            return False

        # If it is a normal confirmed BSQ output we use the default lookup at the daoState
        tx_output_key = TxOutputKey(parent_transaction.get_tx_id(), output.index)
        if self._dao_state_service.is_tx_output_key_spendable(tx_output_key):
            return True

        # It might be that it is an unconfirmed change output which we allow to be used for spending without requiring a confirmation.
        # We check if we have the output in the dao state, if so we have a confirmed but unspendable output (e.g. confiscated).
        if self._dao_state_service.get_tx_output(tx_output_key):
            return False

        # If we have set the isUnconfirmedSpendable flag to true (default) we check for unconfirmed own change outputs.
        # Only if it's not existing yet in the dao state (unconfirmed) we use our unconfirmedBsqChangeOutputList to
        # check if it is an own change output.
        return (
            self.allow_spend_my_own_unconfirmed_tx_outputs
            and self._unconfirmed_bsq_change_output_list_service.has_transaction_output(
                output
            )
        )

    # For BSQ we do not check for dust attack utxos as they are 5.46 BSQ and a considerable value.
    # The default 546 sat dust limit is handled in the BitcoinJ side anyway.
    def is_dust_attack_utxo(self, output: "TransactionOutput") -> bool:
        return False
