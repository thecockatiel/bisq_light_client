from typing import TYPE_CHECKING, Optional

from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.node.parser.op_return_parser import OpReturnParser
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bisq.core.dao.node.parser.temp_tx_output import TempTxOutput
    from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.state.dao_state_service import DaoStateService

logger = get_logger(__name__)

class TxOutputParser:
    """
    Checks if an output is a BSQ output and apply state change.

    With block 602500 (about 4 weeks after v1.2.0 release) we enforce a new rule which represents a
    hard fork. Not updated nodes would see an out of sync dao state hash if a relevant transaction would
    happen again.
    Further (highly unlikely) consequences could be:
    If the BSQ output would be sent to a BSQ address the old client would accept that even it is
    invalid according to the new rules. But sending such an output would require a manually crafted tx
    (not possible in the UI). Worst case a not updated user would buy invalid BSQ but that is not possible as we
    enforce update to 1.2.0 for trading a few days after release as that release introduced the new trade protocol
    and protection tool. Only if both traders would have deactivated filter messages they could trade.

    Problem description:
    We did not apply the check to not allow BSQ outputs after we had detected a BTC output.
    The supported BSQ transactions did not support such cases anyway but we missed an edge case:
    A trade fee tx in case when the BTC input matches exactly the BTC output
    (or BTC change was <= the miner fee) and the BSQ fee was > the miner fee. Then we
    create a change output after the BTC output (using an address from the BTC wallet) and as
    available BSQ was >= as spent BSQ it was considered a valid BSQ output.
    There have been observed 5 such transactions where 4 got spent later to a BTC address and by that burned
    the pending BSQ (spending amount was higher than sending amount). One was still unspent.
    The BSQ was sitting in the BTC wallet so not even visible as BSQ to the user.
    If the user would have crafted a custom BSQ tx he could have avoided that the full trade fee was burned.

    Not a universal rule:
    We cannot enforce the rule that no BSQ output is permitted to all possible transactions because there can be cases
    where we need to permit this case.
    For instance in case we confiscate a lockupTx we have usually 2 BSQ outputs: The first one is the bond which
    should be confiscated and the second one is the BSQ change output.
    At confiscating we set the first to TxOutputType.BTC_OUTPUT but we do not want to confiscate
    the second BSQ change output as well. So we do not apply the rule that no BSQ is allowed once a BTC output is
    found. Theoretically other transactions could be confiscated as well and all BSQ tx which allow > 1 BSQ outputs
    would have the same issue as well if the first output gets confiscated.
    We also don't enforce the rule for irregular or invalid txs which are usually set and detected at the end of
    the tx parsing which is done in the TxParser. Blind vote and LockupTx with invalid OpReturn would be such cases
    where we don't want to invalidate the change output (See comments in TxParser).

    Most transactions created in Bisq (Proposal, blind vote and lockup,...) have only 1 or 2 BSQ
    outputs but we do not enforce a limit of max. 2 transactions in the parser.
    We leave for now that flexibility but it should not be considered as a rule. We might strengthen
    it any time if we find a reason for that (e.g. attack risk) and add checks that no more
    BSQ outputs are permitted for those txs.
    Some transactions like issuance, vote reveal and unlock have exactly 1 BSQ output and that rule
    is enforced.
    """

    ACTIVATE_HARD_FORK_1_HEIGHT_MAINNET = 605000
    ACTIVATE_HARD_FORK_1_HEIGHT_TESTNET = 1583054
    ACTIVATE_HARD_FORK_1_HEIGHT_REGTEST = 1

    def __init__(self, dao_state_service: "DaoStateService"):
        self._dao_state_service = dao_state_service

        self.available_input_value: int = 0
        self.unlock_block_height: int = 0
        self.optional_spent_lockup_tx_output: Optional["TxOutput"] = None

        self.bsq_output_found: bool = False
        self.optional_op_return_type: Optional["OpReturnType"] = None
        self.optional_issuance_candidate: Optional["TempTxOutput"] = None
        self.optional_blind_vote_lock_stake_output: Optional["TempTxOutput"] = None
        self.optional_vote_reveal_unlock_stake_output: Optional["TempTxOutput"] = None
        self.optional_lockup_output: Optional["TempTxOutput"] = None
        self.optional_op_return_index: Optional[int] = None

        self._lock_time: int = 0
        self._utxo_candidates: list["TempTxOutput"] = []
        self._prohibit_more_bsq_outputs: bool = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def process_op_return_output(self, temp_tx_output: "TempTxOutput"):
        op_return_data = temp_tx_output.op_return_data
        assert op_return_data is not None, "op_return_data must not be None"

        tx_output_type = OpReturnParser.get_tx_output_type(temp_tx_output)
        temp_tx_output.tx_output_type = tx_output_type

        self.optional_op_return_type = TxOutputParser.get_mapped_op_return_type(
            tx_output_type
        )

        if self.optional_op_return_type:
            self.optional_op_return_index = temp_tx_output.index

        # If we have a LOCKUP opReturn output we save the lockTime to apply it later to the LOCKUP output.
        # We keep that data in that other output as it makes parsing of the UNLOCK tx easier.
        if self.optional_op_return_type == OpReturnType.LOCKUP:
            self._lock_time = BondConsensus.get_lock_time(op_return_data)

    def process_tx_output(self, temp_tx_output: "TempTxOutput"):
        # We do not expect here an opReturn output as we do not get called on the last output. Any opReturn at
        # another output index is invalid.
        if temp_tx_output.is_op_return_output:
            temp_tx_output.tx_output_type = TxOutputType.INVALID_OUTPUT
            return

        if not self._dao_state_service.is_confiscated_output(temp_tx_output.get_key()):
            tx_output_value = temp_tx_output.value
            index = temp_tx_output.index
            if self._is_unlock_bond_tx(tx_output_value, index):
                # We need to handle UNLOCK transactions separately as they don't follow the pattern on spending BSQ
                # The LOCKUP BSQ is burnt unless the output exactly matches the input, that would cause the
                # output to not be BSQ output at all
                self._handle_unlock_bond_tx(temp_tx_output)
            elif self._is_btc_output_of_burn_fee_tx(temp_tx_output):
                # In case we have the opReturn for a burn fee tx all outputs after 1st output are considered BTC
                self._handle_btc_output(temp_tx_output, index)
            elif self._is_hard_fork_activated(temp_tx_output) and self._is_issuance_candidate_tx_output(temp_tx_output):
                # After the hard fork activation we fix a bug with a transaction which would have interpreted the
                # issuance output as BSQ if the available_input_value was >= issuance amount.
                # Such a tx was never created but as we don't know if it will happen before activation date we cannot
                # enforce the bug fix which represents a rule change before the activation date.
                self._handle_issuance_candidate_output(temp_tx_output)
            elif self.available_input_value > 0 and self.available_input_value >= tx_output_value:
                if self._is_hard_fork_activated(temp_tx_output) and self._prohibit_more_bsq_outputs:
                    self._handle_btc_output(temp_tx_output, index)
                else:
                    self._handle_bsq_output(temp_tx_output, index, tx_output_value)
            else:
                self._handle_btc_output(temp_tx_output, index)
        else:
            logger.warning(f"TxOutput {temp_tx_output.get_key()} is confiscated")
            # We only burn that output
            self.available_input_value -= temp_tx_output.value

            # We must not set prohibit_more_bsq_outputs at confiscation transactions as optional
            # BSQ change output (output 2) must not be confiscated.
            temp_tx_output.tx_output_type = TxOutputType.BTC_OUTPUT

    def commit_utxo_candidates(self):
        for output in self._utxo_candidates:
            self._dao_state_service.add_unspent_tx_output(
                TxOutput.from_temp_output(output)
            )

    def invalidate_utxo_candidates(self):
        # We do not need to apply prohibit_more_bsq_outputs as all spendable outputs are set to BTC_OUTPUT anyway.
        for output in self._utxo_candidates:
            output.tx_output_type = TxOutputType.BTC_OUTPUT

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _is_unlock_bond_tx(self, tx_output_value: int, index: int) -> bool:
        # We require that the input value is exactly the available value and the output value
        return (
            index == 0
            and self.available_input_value == tx_output_value
            and self.optional_spent_lockup_tx_output is not None
            and self.optional_spent_lockup_tx_output.value == tx_output_value
        )

    def _handle_unlock_bond_tx(self, temp_tx_output: "TempTxOutput"):
        check_argument(
            self.optional_spent_lockup_tx_output is not None,
            "optional_spent_lockup_tx_output must be present",
        )
        self.available_input_value -= self.optional_spent_lockup_tx_output.value

        temp_tx_output.tx_output_type = TxOutputType.UNLOCK_OUTPUT
        temp_tx_output.unlock_block_height = self.unlock_block_height
        self._utxo_candidates.append(temp_tx_output)

        self.bsq_output_found = True

        # We do not permit more BSQ outputs after the unlock txo as we don't expect additional BSQ outputs.
        self._prohibit_more_bsq_outputs = True

    def _is_btc_output_of_burn_fee_tx(self, temp_tx_output: "TempTxOutput") -> bool:
        if self.optional_op_return_type:
            index = temp_tx_output.index
            if self.optional_op_return_type == OpReturnType.UNDEFINED:
                pass
            elif self.optional_op_return_type == OpReturnType.PROPOSAL:
                if self._is_hard_fork_activated(temp_tx_output):
                    # We enforce a mandatory BSQ change output.
                    # We need that as similar to ASSET_LISTING_FEE and PROOF_OF_BURN
                    # we could not distinguish between 2 structurally same transactions otherwise (only way here
                    # would be to check the proposal fee as that is known from the params).
                    return index >= 1
            elif self.optional_op_return_type == OpReturnType.COMPENSATION_REQUEST:
                pass
            elif self.optional_op_return_type == OpReturnType.REIMBURSEMENT_REQUEST:
                pass
            elif self.optional_op_return_type == OpReturnType.BLIND_VOTE:
                if self._is_hard_fork_activated(temp_tx_output):
                    # After the hard fork activation we fix a bug with a transaction which would have interpreted the
                    # burned vote fee output as BSQ if the vote fee was >= miner fee.
                    # Such a tx was never created but as we don't know if it will happen before activation date we cannot
                    # enforce the bug fix which represents a rule change before the activation date.

                    # If it is the vote stake output we return false.
                    if index == 0:
                        return False

                    # There must be a vote fee left
                    if self.available_input_value <= 0:
                        return False

                    # Burned BSQ output is last output before opReturn.
                    # We could have also a BSQ change output as last output before opReturn but that will
                    # be detected at blindVoteFee check.
                    # We always have the BSQ change before the burned BSQ output if both are present.
                    check_argument(
                        self.optional_op_return_index is not None,
                        "optional_op_return_index must be present",
                    )
                    if index != self.optional_op_return_index - 1:
                        return False

                    # Without checking the fee we would not be able to distinguish between 2 structurally same transactions, one
                    # where the output is burned BSQ and one where it is a BSQ change output.
                    blind_vote_fee = self._dao_state_service.get_param_value_as_coin(
                        Param.BLIND_VOTE_FEE, temp_tx_output.block_height
                    ).value
                    return self.available_input_value == blind_vote_fee
            elif self.optional_op_return_type == OpReturnType.VOTE_REVEAL:
                pass
            elif self.optional_op_return_type == OpReturnType.LOCKUP:
                pass
            elif self.optional_op_return_type in [
                OpReturnType.ASSET_LISTING_FEE,
                OpReturnType.PROOF_OF_BURN,
            ]:
                # Asset listing fee and proof of burn tx are structurally the same.

                # We need to require one BSQ change output as we could otherwise not be able to distinguish between 2
                # structurally same transactions where only the BSQ fee is different. In case of asset listing fee and proof of
                # burn it is a user input, so it is not known to the parser, instead we derive the burned fee from the parser.
                # In case of proposal fee we could derive it from the params.

                # Case 1: 10 BSQ fee to burn
                # In: 17 BSQ
                # Out: BSQ change 7 BSQ -> valid BSQ
                # Out: OpReturn
                # Miner fee: 1000 sat  (10 BSQ burned)

                # Case 2: 17 BSQ fee to burn
                # In: 17 BSQ
                # Out: burned BSQ change 7 BSQ -> BTC (7 BSQ burned)
                # Out: OpReturn
                # Miner fee: 1000 sat  (10 BSQ burned)
                return index >= 1
        return False

    def _is_issuance_candidate_tx_output(self, temp_tx_output: "TempTxOutput") -> bool:
        # If we have BSQ left as fee and we are at the second output we interpret it as a compensation request output.
        return (
            self.available_input_value > 0
            and temp_tx_output.index == 1
            and self.optional_op_return_type is not None
            and self.optional_op_return_type
            in [OpReturnType.COMPENSATION_REQUEST, OpReturnType.REIMBURSEMENT_REQUEST]
        )

    def _handle_issuance_candidate_output(self, temp_tx_output: "TempTxOutput"):
        # We do not permit more BSQ outputs after the issuance candidate.
        self._prohibit_more_bsq_outputs = True

        # We store the candidate but we don't apply the TxOutputType yet as we need to verify the fee after all
        # outputs are parsed and check the phase. The TxParser will do that.
        self.optional_issuance_candidate = temp_tx_output

    def _handle_bsq_output(
        self, temp_tx_output: "TempTxOutput", index: int, tx_output_value: int
    ):
        # Update the input balance.
        self.available_input_value -= tx_output_value

        is_first_output = index == 0

        op_return_type_candidate = self.optional_op_return_type

        if is_first_output and op_return_type_candidate == OpReturnType.BLIND_VOTE:
            tx_output_type = TxOutputType.BLIND_VOTE_LOCK_STAKE_OUTPUT
            self.optional_blind_vote_lock_stake_output = temp_tx_output
        elif is_first_output and op_return_type_candidate == OpReturnType.VOTE_REVEAL:
            tx_output_type = TxOutputType.VOTE_REVEAL_UNLOCK_STAKE_OUTPUT
            self.optional_vote_reveal_unlock_stake_output = temp_tx_output

            # We do not permit more BSQ outputs after the VOTE_REVEAL_UNLOCK_STAKE_OUTPUT.
            self._prohibit_more_bsq_outputs = True
        elif is_first_output and op_return_type_candidate == OpReturnType.LOCKUP:
            tx_output_type = TxOutputType.LOCKUP_OUTPUT

            # We store the lockTime in the output which will be used as input for an unlock tx.
            # That makes parsing of that data easier as if we would need to access it from the opReturn output of
            # that tx.
            temp_tx_output.lock_time = self._lock_time
            self.optional_lockup_output = temp_tx_output
        else:
            tx_output_type = TxOutputType.BSQ_OUTPUT

        temp_tx_output.tx_output_type = tx_output_type
        self._utxo_candidates.append(temp_tx_output)

        self.bsq_output_found = True

    def _handle_btc_output(self, temp_tx_output: "TempTxOutput", index: int):
        if self._is_hard_fork_activated(temp_tx_output):
            temp_tx_output.tx_output_type = TxOutputType.BTC_OUTPUT

            # For regular transactions we don't permit BSQ outputs after a BTC output was detected.
            self._prohibit_more_bsq_outputs = True
        else:
            # If we have BSQ left as fee and we are at the second output it might be a compensation request output.
            # We store the candidate but we don't apply the TxOutputType yet as we need to verify the fee after all
            # outputs are parsed and check the phase. The TxParser will do that.
            if (
                self.available_input_value > 0
                and index == 1
                and self.optional_op_return_type is not None
                and self.optional_op_return_type
                in [
                    OpReturnType.COMPENSATION_REQUEST,
                    OpReturnType.REIMBURSEMENT_REQUEST,
                ]
            ):
                self.optional_issuance_candidate = temp_tx_output

                # We do not permit more BSQ outputs after the issuance candidate.
                self._prohibit_more_bsq_outputs = True
            else:
                temp_tx_output.tx_output_type = TxOutputType.BTC_OUTPUT

                # For regular transactions we don't permit BSQ outputs after a BTC output was detected.
                self._prohibit_more_bsq_outputs = True

    def _is_hard_fork_activated(self, temp_tx_output: "TempTxOutput") -> bool:
        return temp_tx_output.block_height >= self._get_activate_hard_fork_1_height()

    def _get_activate_hard_fork_1_height(self) -> int:
        if Config.BASE_CURRENCY_NETWORK_VALUE.is_mainnet():
            return TxOutputParser.ACTIVATE_HARD_FORK_1_HEIGHT_MAINNET
        elif Config.BASE_CURRENCY_NETWORK_VALUE.is_testnet():
            return TxOutputParser.ACTIVATE_HARD_FORK_1_HEIGHT_TESTNET
        else:
            return TxOutputParser.ACTIVATE_HARD_FORK_1_HEIGHT_REGTEST

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Static
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def get_mapped_op_return_type(
        output_type: TxOutputType,
    ) -> Optional["OpReturnType"]:
        if output_type == TxOutputType.PROPOSAL_OP_RETURN_OUTPUT:
            return OpReturnType.PROPOSAL
        elif output_type == TxOutputType.COMP_REQ_OP_RETURN_OUTPUT:
            return OpReturnType.COMPENSATION_REQUEST
        elif output_type == TxOutputType.REIMBURSEMENT_OP_RETURN_OUTPUT:
            return OpReturnType.REIMBURSEMENT_REQUEST
        elif output_type == TxOutputType.BLIND_VOTE_OP_RETURN_OUTPUT:
            return OpReturnType.BLIND_VOTE
        elif output_type == TxOutputType.VOTE_REVEAL_OP_RETURN_OUTPUT:
            return OpReturnType.VOTE_REVEAL
        elif output_type == TxOutputType.LOCKUP_OP_RETURN_OUTPUT:
            return OpReturnType.LOCKUP
        elif output_type == TxOutputType.ASSET_LISTING_FEE_OP_RETURN_OUTPUT:
            return OpReturnType.ASSET_LISTING_FEE
        elif output_type == TxOutputType.PROOF_OF_BURN_OP_RETURN_OUTPUT:
            return OpReturnType.PROOF_OF_BURN
        else:
            return None
