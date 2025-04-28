from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.dao.state.model.blockchain.spent_info import SpentInfo
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType


if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.state.dao_state_service import DaoStateService


class TxInputParser:
    """Processes TxInput and add input value to available balance if the input is a valid BSQ input."""

    def __init__(self, dao_state_service: "DaoStateService"):
        self._dao_state_service = dao_state_service
        self.accumulated_input_value = 0
        self.burnt_bond_value = 0
        self.unlock_block_height = 0
        self.optional_spent_lockup_tx_output: Optional["TxOutput"] = None
        self.is_unlock_input_valid = True
        self._num_vote_reveal_inputs = 0
        self.logger = get_ctx_logger(__name__)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def process(
        self,
        tx_output_key: "TxOutputKey",
        block_height: int,
        tx_id: str,
        input_index: int,
    ):
        if not self._dao_state_service.is_confiscated_output(tx_output_key):
            connected_tx_output = self._dao_state_service.get_unspent_tx_output(
                tx_output_key
            )
            if connected_tx_output:
                input_value = connected_tx_output.value
                self.accumulated_input_value += input_value

                # If we are spending an output from a blind vote tx marked as VOTE_STAKE_OUTPUT we save it in our parsingModel
                # for later verification at the outputs of a reveal tx.
                connected_tx_output_type = connected_tx_output.tx_output_type
                if (
                    connected_tx_output_type
                    == TxOutputType.BLIND_VOTE_LOCK_STAKE_OUTPUT
                ):
                    self._num_vote_reveal_inputs += 1
                    # The connected tx output of the blind vote tx is our input for the reveal tx.
                    # We allow only one input from any blind vote tx otherwise the vote reveal tx is invalid.
                    if not self._is_vote_reveal_input_valid:
                        self.logger.warning(
                            "We have a tx which has >1 connected txOutputs marked as BLIND_VOTE_LOCK_STAKE_OUTPUT. This is not a valid BSQ tx."
                        )
                elif connected_tx_output_type == TxOutputType.LOCKUP_OUTPUT:
                    # A LOCKUP BSQ txOutput is spent to a corresponding UNLOCK
                    # txInput. The UNLOCK can only be spent after lockTime blocks has passed.
                    self.is_unlock_input_valid = (
                        self.optional_spent_lockup_tx_output is None
                    )
                    if self.is_unlock_input_valid:
                        self.optional_spent_lockup_tx_output = connected_tx_output
                        self.unlock_block_height = (
                            block_height + connected_tx_output.lock_time
                        )
                    else:
                        self.logger.warning(
                            "We have a tx which has >1 connected txOutputs marked as LOCKUP_OUTPUT. This is not a valid BSQ tx."
                        )
                elif connected_tx_output_type == TxOutputType.UNLOCK_OUTPUT:
                    # This txInput is Spending an UNLOCK txOutput
                    unlock_block_height = connected_tx_output.unlock_block_height
                    if block_height < unlock_block_height:
                        self.accumulated_input_value -= input_value
                        self.burnt_bond_value += input_value
                        self.logger.warning(
                            f"We got a tx which spends the output from an unlock tx but before the "
                            f"unlockTime has passed. That leads to burned BSQ! "
                            f"blockHeight={block_height}, unLockHeight={unlock_block_height}"
                        )

                self._dao_state_service.set_spent_info(
                    connected_tx_output.get_key(),
                    SpentInfo(block_height, tx_id, input_index),
                )
                self._dao_state_service.remove_unspent_tx_output(connected_tx_output)
        else:
            self.logger.warning(
                f"Connected txOutput {tx_output_key} at input {input_index} of txId {tx_id} is confiscated"
            )

    @property
    def _is_vote_reveal_input_valid(self) -> bool:
        return self._num_vote_reveal_inputs == 1
