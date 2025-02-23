from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.node.genesis_tx_parser import GenesisTxParser
from bisq.core.dao.node.parser.tx_input_parser import TxInputParser
from bisq.core.dao.node.parser.tx_output_parser import TxOutputParser
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from bisq.core.dao.state.model.blockchain.tx import Tx
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.dao.node.full.raw_tx import RawTx
    from bisq.core.dao.node.parser.temp_tx import TempTx
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService


logger = get_logger(__name__)


class TxParser:
    """Verifies if a given transaction is a BSQ transaction."""

    def __init__(
        self, period_service: "PeriodService", dao_state_service: "DaoStateService"
    ):
        self._period_service = period_service
        self._dao_state_service = dao_state_service
        self._tx_output_parser: Optional["TxOutputParser"] = None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def find_tx(
        self,
        raw_tx: "RawTx",
        genesis_tx_id: str,
        genesis_block_height: int,
        genesis_total_supply: Coin,
    ) -> Optional[Tx]:
        if GenesisTxParser.is_genesis(raw_tx, genesis_tx_id, genesis_block_height):
            return GenesisTxParser.get_genesis_tx(
                raw_tx, genesis_total_supply, self._dao_state_service
            )
        else:
            return self._find_tx(raw_tx)

    # Apply state changes to tx, inputs and outputs
    # return Tx if any input contained BSQ
    # Any tx with BSQ input is a BSQ tx.
    # There might be txs without any valid BSQ txOutput but we still keep track of it,
    # for instance to calculate the total burned BSQ.
    def _find_tx(self, raw_tx: "RawTx") -> Optional[Tx]:
        block_height = raw_tx.block_height
        temp_tx = TempTx.from_raw_tx(raw_tx)

        # ****************************************************************************************
        # Parse Inputs
        # ****************************************************************************************

        tx_input_parser = TxInputParser(self._dao_state_service)
        for input_index, tx_input in enumerate(temp_tx.tx_inputs):
            output_key = tx_input.get_connected_tx_output_key()
            tx_input_parser.process(output_key, block_height, raw_tx.id, input_index)

        # Results from tx_input_parser
        accumulated_input_value = tx_input_parser.accumulated_input_value
        burnt_bond_value = tx_input_parser.burnt_bond_value
        unlock_input_valid = tx_input_parser.is_unlock_input_valid
        unlock_block_height = tx_input_parser.unlock_block_height
        optional_spent_lockup_tx_output = (
            tx_input_parser.optional_spent_lockup_tx_output
        )

        has_bsq_inputs = accumulated_input_value > 0
        has_burnt_bond = burnt_bond_value > 0

        # If we don't have any BSQ in our input and we don't have burnt bonds we do not consider the tx as a BSQ tx.
        if not has_bsq_inputs and not has_burnt_bond:
            return None

        # ****************************************************************************************
        # Parse Outputs
        # ****************************************************************************************

        self._tx_output_parser = TxOutputParser(self._dao_state_service)
        self._tx_output_parser.available_input_value = accumulated_input_value
        self._tx_output_parser.unlock_block_height = unlock_block_height
        self._tx_output_parser.optional_spent_lockup_tx_output = (
            optional_spent_lockup_tx_output
        )

        outputs = temp_tx.temp_tx_outputs
        # We start with last output as that might be an OP_RETURN output and gives us the specific tx type, so it is
        # easier and cleaner at parsing the other outputs to detect which kind of tx we deal with.
        last_index = len(outputs) - 1
        last_non_op_return_index = last_index
        if outputs[last_index].is_op_return_output:
            self._tx_output_parser.process_op_return_output(outputs[last_index])
            last_non_op_return_index -= 1

        # We need to consider the order of the outputs. An output is a BSQ utxo as long there is enough input value
        # We iterate all outputs (excluding an optional opReturn).
        for index in range(last_non_op_return_index + 1):
            self._tx_output_parser.process_tx_output(outputs[index])

        # Results from tx_output_parser
        remaining_input_value = self._tx_output_parser.available_input_value
        optional_op_return_type = self._tx_output_parser.optional_op_return_type
        bsq_output_found = self._tx_output_parser.bsq_output_found

        burnt_bsq = remaining_input_value + burnt_bond_value
        has_burnt_bsq = burnt_bsq > 0
        if has_burnt_bsq:
            temp_tx.burnt_bsq = burnt_bsq

        # ****************************************************************************************
        # Verify and apply txType and txOutputTypes after we have all outputs parsed
        # ****************************************************************************************

        self._apply_tx_type_and_tx_output_type(
            block_height, temp_tx, remaining_input_value
        )
        if temp_tx.tx_type not in [TxType.IRREGULAR, TxType.INVALID]:
            tx_type = self.evaluate_tx_type(
                temp_tx, optional_op_return_type, has_burnt_bsq, unlock_input_valid
            )
            temp_tx.tx_type = tx_type
        else:
            tx_type = temp_tx.tx_type

        if self.is_tx_invalid(temp_tx, bsq_output_found, has_burnt_bond):
            temp_tx.tx_type = TxType.INVALID
            # We consider all BSQ inputs as burned if the tx is invalid.
            temp_tx.burnt_bsq = accumulated_input_value
            self._tx_output_parser.invalidate_utxo_candidates()
            logger.warning(
                f"We have destroyed BSQ because of an invalid tx. Burned BSQ={accumulated_input_value / 100}, tx={temp_tx}",
            )
        elif tx_type == TxType.IRREGULAR:
            logger.warning(f"We have an irregular tx {temp_tx}")
            self._tx_output_parser.commit_utxo_candidates()
        else:
            self._tx_output_parser.commit_utxo_candidates()

        return Tx.from_temp_tx(temp_tx)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _apply_tx_type_and_tx_output_type(
        self, block_height: int, temp_tx: "TempTx", bsq_fee: int
    ):
        """
        This method verifies after all outputs are parsed if the opReturn type and the optional txOutputs required for
        certain use cases are valid.
        It verifies also if the fee is correct (if required) and if the phase is correct (if relevant).
        We set the txType as well as the txOutputType of the relevant outputs.
        """
        op_return_type = self._tx_output_parser.optional_op_return_type
        if op_return_type:
            if op_return_type == OpReturnType.PROPOSAL:
                self._process_proposal(block_height, temp_tx, bsq_fee)
            elif op_return_type in [
                OpReturnType.COMPENSATION_REQUEST,
                OpReturnType.REIMBURSEMENT_REQUEST,
            ]:
                self._process_issuance(block_height, temp_tx, bsq_fee)
            elif op_return_type == OpReturnType.BLIND_VOTE:
                self._process_blind_vote(block_height, temp_tx, bsq_fee)
            elif op_return_type == OpReturnType.VOTE_REVEAL:
                # We do not check phase or cycle as a late voteReveal tx is considered a valid BSQ tx.
                # The vote result though will ignore such votes.
                pass
            elif op_return_type in [
                OpReturnType.LOCKUP,
                OpReturnType.ASSET_LISTING_FEE,
                OpReturnType.PROOF_OF_BURN,
            ]:
                # do nothing
                pass

        # We need to check if any tempTxOutput is available and if so and the OpReturn data is invalid we
        # set the output to a BTC output. We must not use `if else` cases here!
        if op_return_type not in [
            OpReturnType.COMPENSATION_REQUEST,
            OpReturnType.REIMBURSEMENT_REQUEST,
        ]:
            # We applied already the check to not permit further BSQ outputs after the issuanceCandidate in the
            # tx_output_parser so we don't need to do any additional check here when we change to BTC_OUTPUT.
            if self._tx_output_parser.optional_issuance_candidate:
                self._tx_output_parser.optional_issuance_candidate.tx_output_type = (
                    TxOutputType.BTC_OUTPUT
                )

        if op_return_type != OpReturnType.BLIND_VOTE:
            if self._tx_output_parser.optional_blind_vote_lock_stake_output:
                # We cannot apply the rule to not allow BSQ outputs after a BTC output as the 2nd output is an
                # optional BSQ change output and we don't want to burn that in case the opReturn is invalid.
                self._tx_output_parser.optional_blind_vote_lock_stake_output.tx_output_type = (
                    TxOutputType.BTC_OUTPUT
                )

        if op_return_type != OpReturnType.VOTE_REVEAL:
            if self._tx_output_parser.optional_vote_reveal_unlock_stake_output:
                # We do not apply the rule to not allow BSQ outputs after a BTC output here because we expect only
                # one BSQ output anyway.
                self._tx_output_parser.optional_vote_reveal_unlock_stake_output.tx_output_type = (
                    TxOutputType.BTC_OUTPUT
                )

        if op_return_type != OpReturnType.LOCKUP:
            if self._tx_output_parser.optional_lockup_output:
                # We cannot apply the rule to not allow BSQ outputs after a BTC output as the 2nd output is an
                # optional BSQ change output and we don't want to burn that in case the opReturn is invalid.
                self._tx_output_parser.optional_lockup_output.tx_output_type = (
                    TxOutputType.BTC_OUTPUT
                )

    def _process_proposal(self, block_height: int, temp_tx: "TempTx", bsq_fee: int):
        is_fee_and_phase_valid = self._is_fee_and_phase_valid(
            temp_tx.id,
            block_height,
            bsq_fee,
            DaoPhase.Phase.PROPOSAL,
            Param.PROPOSAL_FEE,
        )
        if not is_fee_and_phase_valid:
            # We tolerate such an incorrect tx and do not burn the BSQ
            temp_tx.tx_type = TxType.IRREGULAR

    def _process_issuance(self, block_height: int, temp_tx: "TempTx", bsq_fee: int):
        is_fee_and_phase_valid = self._is_fee_and_phase_valid(
            temp_tx.id,
            block_height,
            bsq_fee,
            DaoPhase.Phase.PROPOSAL,
            Param.PROPOSAL_FEE,
        )
        issuance_candidate = self._tx_output_parser.optional_issuance_candidate
        if is_fee_and_phase_valid:
            if issuance_candidate:
                # Now after we have validated the fee and phase we will apply the TxOutputType
                issuance_candidate.tx_output_type = (
                    TxOutputType.ISSUANCE_CANDIDATE_OUTPUT
                )
            else:
                logger.warning(
                    "It can be that we have an opReturn which is correct from its structure but the whole tx "
                    "is not valid as the issuanceCandidate is not there. "
                    "As the BSQ fee is set it must be either a buggy tx or a manually crafted invalid tx."
                )
                # Even though the request part is invalid the BSQ transfer and change output should still be valid
                # as long as the BSQ change <= BSQ inputs.
                # We tolerate such an incorrect tx and do not burn the BSQ
                temp_tx.tx_type = TxType.IRREGULAR
        else:
            # This could be a valid compensation request that failed to be included in a block during the
            # correct phase due to no fault of the user. We must not burn the change as long as the BSQ inputs
            # cover the value of the outputs.
            # We tolerate such an incorrect tx and do not burn the BSQ
            temp_tx.tx_type = TxType.IRREGULAR

            # Make sure the optionalIssuanceCandidate is set to BTC
            # We applied already the check to not permit further BSQ outputs after the issuanceCandidate in the
            # txOutputParser so we don't need to do any additional check here when we change to BTC_OUTPUT.
            if issuance_candidate:
                issuance_candidate.tx_output_type = TxOutputType.BTC_OUTPUT
            # Empty case is a possible valid case where a random tx matches our opReturn rules but it is not a
            # valid BSQ tx.

    def _process_blind_vote(self, block_height: int, temp_tx: "TempTx", bsq_fee: int):
        is_fee_and_phase_valid = self._is_fee_and_phase_valid(
            temp_tx.id,
            block_height,
            bsq_fee,
            DaoPhase.Phase.BLIND_VOTE,
            Param.BLIND_VOTE_FEE,
        )
        if not is_fee_and_phase_valid:
            # We tolerate such an incorrect tx and do not burn the BSQ
            temp_tx.tx_type = TxType.IRREGULAR

            # Set the stake output from BLIND_VOTE_LOCK_STAKE_OUTPUT to BSQ
            if (
                self._tx_output_parser
                and self._tx_output_parser.optional_blind_vote_lock_stake_output
            ):
                self._tx_output_parser.optional_blind_vote_lock_stake_output.tx_output_type = (
                    TxOutputType.BSQ_OUTPUT
                )
                # "None" case is a possible valid case where a random tx matches our opReturn rules but it is not a
                # valid BSQ tx.

    def _is_fee_and_phase_valid(
        self,
        tx_id: str,
        block_height: int,
        bsq_fee: int,
        phase: "DaoPhase.Phase",
        param: "Param",
    ) -> bool:
        # The leftover BSQ balance from the inputs is the BSQ fee in case we are in an OP_RETURN output

        if not self._period_service.is_in_phase(block_height, phase):
            logger.warning(
                f"Tx with ID {tx_id} is not in required phase ({phase}). blockHeight={block_height}"
            )
            return False

        param_value = self._dao_state_service.get_param_value_as_coin(
            param, block_height
        ).value
        is_fee_correct = bsq_fee == param_value
        if not is_fee_correct:
            logger.warning(
                f"Invalid fee. used fee={bsq_fee}, required fee={param_value}, txId={tx_id}"
            )
        return is_fee_correct

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Static methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Performs various checks for an invalid tx
    @staticmethod
    def is_tx_invalid(
        temp_tx: "TempTx", bsq_output_found: bool, burnt_bond_value: bool
    ) -> bool:
        if temp_tx.tx_type == TxType.INVALID:
            # We got already set the invalid type in earlier checks and return early.
            return True

        # We don't allow multiple opReturn outputs (they are non-standard but to be safe lets check it)
        num_op_return_outputs = sum(
            1 for output in temp_tx.temp_tx_outputs if output.is_op_return_output
        )
        if num_op_return_outputs > 1:
            logger.warning(
                f"Invalid tx. We have multiple opReturn outputs. tx={temp_tx}"
            )
            return True

        if (
            temp_tx.tx_type
            in [TxType.COMPENSATION_REQUEST, TxType.REIMBURSEMENT_REQUEST]
        ) and not bsq_output_found:
            logger.warning(
                f"Invalid Tx: A compensation or reimbursement tx requires 1 BSQ output. Tx={temp_tx}"
            )
            return True

        if burnt_bond_value:
            logger.warning(f"Invalid Tx: Bond value was burnt. tx={temp_tx}")
            return True

        if any(
            output.tx_output_type
            in [TxOutputType.UNDEFINED_OUTPUT, TxOutputType.INVALID_OUTPUT]
            for output in temp_tx.temp_tx_outputs
        ):
            logger.warning(
                f"Invalid Tx: We have undefined or invalid txOutput types. tx={temp_tx}"
            )
            return True

        return False

    @staticmethod
    def evaluate_tx_type(
        temp_tx: "TempTx",
        optional_op_return_type: Optional[OpReturnType],
        has_burnt_bsq: bool,
        is_unlock_input_valid: bool,
    ) -> "TxType":
        """Retrieve the type of the transaction, assuming it is relevant to bisq."""
        if optional_op_return_type:
            # We use the opReturnType to find the txType
            return TxParser.evaluate_tx_type_from_op_return_type(
                temp_tx, optional_op_return_type
            )

        # No opReturnType, so we check for the remaining possible cases
        if has_burnt_bsq:
            # PAY_TRADE_FEE tx has a fee and no opReturn
            return TxType.PAY_TRADE_FEE

        # UNLOCK tx has no fee, no opReturn but an UNLOCK_OUTPUT at first output.
        if temp_tx.temp_tx_outputs[0].tx_output_type == TxOutputType.UNLOCK_OUTPUT:
            # We check if there have been invalid inputs
            if not is_unlock_input_valid:
                return TxType.INVALID

            return TxType.UNLOCK

        # TRANSFER_BSQ has no fee, no opReturn and no UNLOCK_OUTPUT at first output
        logger.trace("No burned fee and no OP_RETURN, so this is a TRANSFER_BSQ tx.")
        return TxType.TRANSFER_BSQ

    @staticmethod
    def evaluate_tx_type_from_op_return_type(
        temp_tx: "TempTx", op_return_type: OpReturnType
    ) -> "TxType":
        if op_return_type == OpReturnType.PROPOSAL:
            return TxType.PROPOSAL
        elif op_return_type in [
            OpReturnType.COMPENSATION_REQUEST,
            OpReturnType.REIMBURSEMENT_REQUEST,
        ]:
            has_correct_num_outputs = len(temp_tx.temp_tx_outputs) >= 3
            if not has_correct_num_outputs:
                logger.warning(
                    "Compensation/reimbursement request tx need to have at least 3 outputs"
                )
                # Such a transaction cannot be created by the Bisq client and is considered invalid.
                return TxType.INVALID

            issuance_tx_output = temp_tx.temp_tx_outputs[1]
            has_issuance_output = (
                issuance_tx_output.tx_output_type
                == TxOutputType.ISSUANCE_CANDIDATE_OUTPUT
            )
            if not has_issuance_output:
                logger.warning(
                    "Compensation/reimbursement request txOutput type of output at index 1 need to be ISSUANCE_CANDIDATE_OUTPUT. "
                    f"TxOutputType={issuance_tx_output.tx_output_type.name}"
                )
                # Such a transaction cannot be created by the Bisq client and is considered invalid.
                return TxType.INVALID

            return (
                TxType.COMPENSATION_REQUEST
                if op_return_type == OpReturnType.COMPENSATION_REQUEST
                else TxType.REIMBURSEMENT_REQUEST
            )
        elif op_return_type == OpReturnType.BLIND_VOTE:
            return TxType.BLIND_VOTE
        elif op_return_type == OpReturnType.VOTE_REVEAL:
            return TxType.VOTE_REVEAL
        elif op_return_type == OpReturnType.LOCKUP:
            return TxType.LOCKUP
        elif op_return_type == OpReturnType.ASSET_LISTING_FEE:
            return TxType.ASSET_LISTING_FEE
        elif op_return_type == OpReturnType.PROOF_OF_BURN:
            return TxType.PROOF_OF_BURN
        else:
            logger.warning(
                f"We got a BSQ tx with an unknown OP_RETURN. tx={temp_tx}, opReturnType={op_return_type}"
            )
            # We tolerate such an incorrect tx and do not burn the BSQ. We might need that in case we add new
            # opReturn types in future.
            return TxType.IRREGULAR
