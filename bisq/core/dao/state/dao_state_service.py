import itertools
from typing import TYPE_CHECKING, Optional, Union
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
from bisq.core.dao.state.model.dao_state import DaoState
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from bisq.core.dao.state.model.governance.param_change import ParamChange
from bisq.core.util.parsing_utils import ParsingUtils
from bitcoinj.base.coin import Coin
from utils.concurrency import ThreadSafeSet
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.issuance import Issuance
    from bisq.core.dao.state.model.blockchain.spent_info import SpentInfo
    from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
    from bisq.core.dao.state.model.blockchain.tx_input import TxInput
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.state.model.governance.cycle import Cycle
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.util.coin.bsq_formatter import BsqFormatter
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo
    from bisq.core.dao.state.dao_state_listener import DaoStateListener
    from bisq.core.dao.state.model.governance.decrypted_ballots_with_merits import (
        DecryptedBallotsWithMerits,
    )
    from bisq.core.dao.state.model.governance.evaluated_proposal import (
        EvaluatedProposal,
    )


logger = get_logger(__name__)


class DaoStateService(DaoSetupService):
    """Provides access methods to DaoState data."""

    def __init__(
        self,
        dao_state: "DaoState",
        genesis_tx_info: "GenesisTxInfo",
        bsq_formatter: "BsqFormatter",
    ) -> None:
        self.dao_state = dao_state
        self.genesis_tx_info = genesis_tx_info
        self.bsq_formatter = bsq_formatter
        self.dao_state_listeners: ThreadSafeSet["DaoStateListener"] = ThreadSafeSet()
        self.parse_block_chain_complete = False
        self.allow_dao_state_change = False
        self._cached_tx_id_set_by_address: dict[str, set[str]] = {}

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        pass

    def start(self):
        self.allow_dao_state_change = True
        self._assert_dao_state_change()
        self.dao_state.chain_height = self.genesis_tx_info.genesis_block_height

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Snapshot
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def apply_snapshot(self, snapshot: "DaoState"):
        self.allow_dao_state_change = True
        self._assert_dao_state_change()

        logger.info(f"Apply snapshot with chain height {snapshot.chain_height}")

        self.dao_state.chain_height = snapshot.chain_height
        self.dao_state.set_tx_cache(snapshot.tx_cache)

        self.dao_state.clear_and_set_blocks(snapshot.blocks)

        self.dao_state.cycles.clear()
        self.dao_state.cycles.extend(snapshot.cycles)

        self.dao_state.unspent_tx_output_map.clear()
        self.dao_state.unspent_tx_output_map.update(snapshot.unspent_tx_output_map)

        self.dao_state.spent_info_map.clear()
        self.dao_state.spent_info_map.update(snapshot.spent_info_map)

        self.dao_state.confiscated_lockup_tx_list.clear()
        self.dao_state.confiscated_lockup_tx_list.extend(
            snapshot.confiscated_lockup_tx_list
        )

        self.dao_state.issuance_map.clear()
        self.dao_state.issuance_map.update(snapshot.issuance_map)

        self.dao_state.param_change_list.clear()
        self.dao_state.param_change_list.extend(snapshot.param_change_list)

        self.dao_state.evaluated_proposal_list.clear()
        self.dao_state.evaluated_proposal_list.extend(snapshot.evaluated_proposal_list)

        self.dao_state.decrypted_ballots_with_merits_list.clear()
        self.dao_state.decrypted_ballots_with_merits_list.extend(
            snapshot.decrypted_ballots_with_merits_list
        )

    def get_clone(self) -> "DaoState":
        return self.dao_state.get_clone()

    def get_bsq_state_clone_excluding_blocks(self):
        return DaoState.get_bsq_state_clone_excluding_blocks(self.dao_state)

    def get_serialized_state_for_hash_chain(self) -> bytes:
        return self.dao_state.get_serialized_state_for_hash_chain()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // ChainHeight
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def chain_height(self) -> int:
        return self.dao_state.chain_height

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Cycle
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def cycles(self):
        return self.dao_state.cycles

    def add_cycle(self, cycle: "Cycle") -> None:
        self._assert_dao_state_change()
        self.cycles.append(cycle)

    @property
    def current_cycle(self) -> Optional["Cycle"]:
        return self.cycles[-1] if self.cycles else None

    def get_cycle(self, height: int) -> Optional["Cycle"]:
        return next(
            (
                cycle
                for cycle in self.cycles
                if cycle.height_of_first_block <= height <= cycle.height_of_last_block
            ),
            None,
        )

    def get_start_height_of_next_cycle(self, block_height: int) -> Optional[int]:
        cycle = self.get_cycle(block_height)
        return cycle.height_of_last_block + 1 if cycle else None

    def get_start_height_of_current_cycle(self, block_height: int) -> Optional[int]:
        cycle = self.get_cycle(block_height)
        return cycle.height_of_first_block if cycle else None

    def get_next_cycle(self, cycle: "Cycle") -> Optional["Cycle"]:
        return self.get_cycle(cycle.height_of_last_block + 1)

    def get_previous_cycle(self, cycle: "Cycle") -> Optional["Cycle"]:
        return self.get_cycle(cycle.height_of_first_block - 1)

    def get_past_cycle(self, cycle: "Cycle", num_past_cycles: int) -> Optional["Cycle"]:
        previous = None
        current = cycle
        for _ in range(num_past_cycles):
            previous = self.get_previous_cycle(current)
            if previous:
                current = previous
            else:
                break
        return previous

    def get_cycle_at_index(self, index: int) -> Optional["Cycle"]:
        return self.cycles[index]

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Block
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Parser events
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # First we get the blockHeight set
    def on_new_block_height(self, block_height: int) -> None:
        self.allow_dao_state_change = True
        self.dao_state.chain_height = block_height
        for listener in self.dao_state_listeners:
            listener.on_new_block_height(block_height)

    # Second we get the block added with empty txs
    def on_new_block_with_empty_txs(self, block: "Block") -> None:
        self._assert_dao_state_change()
        if not self.dao_state.blocks and block.height != self.genesis_block_height:
            logger.warning(
                "We don't have any blocks yet and we received a block which is not the genesis block. "
                "We ignore that block as the first block needs to be the genesis block. "
                f"That might happen in edge cases at reorgs. Received block={block}"
            )
        else:
            self.dao_state.add_block(block)

            if self.parse_block_chain_complete:
                logger.info(f"New Block added at blockHeight {block.height}")

    # Third we add each successfully parsed BSQ tx to the last block
    def on_new_tx_for_last_block(self, block: "Block", tx: "Tx") -> None:
        self._assert_dao_state_change()

        last_block = self.last_block
        if last_block:
            if block == last_block:
                # We need to ensure that the txs in all blocks are in sync with the txs in our txMap (cache).
                block.add_tx(tx)
                self.dao_state.add_to_tx_cache(tx)
            else:
                # Not clear if this case can happen but at on_new_block_with_empty_txs we handle such a potential edge
                # case as well, so we need to reflect that here as well.
                logger.warning(
                    "Block for parsing does not match last block. That might happen in edge cases at reorgs. "
                    f"Received block={block}"
                )

    # Fourth we get the onParseBlockComplete called after all rawTxs of blocks have been parsed
    def on_parse_block_complete(self, block: "Block") -> None:
        if self.parse_block_chain_complete:
            logger.info(
                f"Parse block completed: Block height {block.height}, {len(block._txs)} BSQ transactions."
            )

        # Need to be called before onParseTxsCompleteAfterBatchProcessing as we use it in
        # VoteResult and other listeners like balances usually listen on onParseTxsCompleteAfterBatchProcessing
        # so we need to make sure that vote result calculation is completed before (e.g. for comp. request to
        # update balance).
        for listener in self.dao_state_listeners:
            listener.on_parse_block_complete(block)

        # We use 2 different handlers as we don't want to update domain listeners during batch processing of all
        # blocks as that causes performance issues. In earlier versions when we updated at each block it took
        # 50 sec. for 4000 blocks, after that change it was about 4 sec.
        # Clients
        if self.parse_block_chain_complete:
            for listener in self.dao_state_listeners:
                listener.on_parse_block_complete_after_batch_processing(block)

        # Here listeners must not trigger any state change in the DAO as we trigger the validation service to
        # generate a hash of the state.
        self.allow_dao_state_change = False
        for listener in self.dao_state_listeners:
            listener.on_dao_state_changed(block)

        if block._txs:
            self._cached_tx_id_set_by_address.clear()

    #  Called after parsing of all pending blocks is completed
    def on_parse_block_chain_complete(self) -> None:
        logger.info("Parse blockchain completed")
        self.parse_block_chain_complete = True

        last_block = self.last_block
        if last_block:
            for listener in self.dao_state_listeners:
                listener.on_parse_block_complete_after_batch_processing(last_block)

        for listener in self.dao_state_listeners:
            listener.on_parse_block_chain_complete()

    @property
    def blocks(self):
        return self.dao_state.blocks

    @property
    def last_block(self):
        if self.dao_state.blocks:
            return self.dao_state.last_block
        else:
            return None

    @property
    def block_height_of_last_block(self) -> int:
        last_block = self.last_block
        return last_block.height if last_block else 0

    @property
    def block_hash_of_last_block(self) -> str:
        last_block = self.last_block
        return last_block.hash if last_block else ""

    def get_block_at_height(self, height: int) -> Optional["Block"]:
        return self.dao_state.blocks_by_height.get(height, None)

    def contains_block(self, block: "Block") -> bool:
        return block in self.blocks

    def get_block_time(self, height: int) -> int:
        block = self.get_block_at_height(height)
        return block.time if block else 0

    def get_blocks_from_block_height(
        self, from_block_height: int, num_max_blocks: int = 2147483647
    ):
        return list(
            self.get_blocks_from_block_height_stream(from_block_height, num_max_blocks)
        )

    def get_blocks_from_block_height_stream(
        self, from_block_height: int, num_max_blocks: int
    ):
        # We limit requests to numMaxBlocks blocks, to avoid performance issues and too
        # large network data in case a node requests too far back in history.
        return itertools.islice(
            (block for block in self.blocks if block.height >= from_block_height),
            num_max_blocks,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Genesis
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def genesis_tx_id(self) -> str:
        return self.genesis_tx_info.genesis_tx_id

    @property
    def genesis_block_height(self) -> int:
        return self.genesis_tx_info.genesis_block_height

    @property
    def genesis_total_supply(self) -> Coin:
        return Coin.value_of(self.genesis_tx_info.genesis_total_supply)

    def get_genesis_tx(self) -> Optional["Tx"]:
        return self.get_tx(self.genesis_tx_id)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_unordered_tx_stream(self):
        # even in java version the name was misleading.
        return iter(self.dao_state.tx_cache.values())

    def get_num_txs(self) -> int:
        return len(self.dao_state.tx_cache)

    def get_invalid_txs(self):
        return [
            tx for tx in self.get_unordered_tx_stream() if tx.tx_type == TxType.INVALID
        ]

    def get_irregular_txs(self):
        return [
            tx
            for tx in self.get_unordered_tx_stream()
            if tx.tx_type == TxType.IRREGULAR
        ]

    def get_tx(self, tx_id: str) -> Optional["Tx"]:
        return self.dao_state.tx_cache.get(tx_id, None)

    def contains_tx(self, tx_id: str) -> bool:
        return self.get_tx(tx_id) is not None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TxType
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_optional_tx_type(self, tx_id: str) -> Optional["TxType"]:
        tx = self.get_tx(tx_id)
        return tx.tx_type if tx else None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BurntFee (trade fee and fee burned at proof of burn)
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_burnt_fee(self, tx_id: str) -> int:
        tx = self.get_tx(tx_id)
        return tx.burnt_fee if tx else 0

    def has_tx_burnt_fee(self, tx_id: str) -> bool:
        return self.get_burnt_fee(tx_id) > 0

    def get_trade_fee_txs(self) -> set["Tx"]:
        return {
            tx
            for tx in self.get_unordered_tx_stream()
            if tx.tx_type == TxType.PAY_TRADE_FEE
        }

    def get_proof_of_burn_txs(self) -> set["Tx"]:
        return {
            tx
            for tx in self.get_unordered_tx_stream()
            if tx.tx_type == TxType.PROOF_OF_BURN
        }

    # Any tx with burned BSQ
    def get_burnt_fee_txs(self) -> set["Tx"]:
        return {tx for tx in self.get_unordered_tx_stream() if tx.burnt_fee > 0}

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TxInput
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_connected_tx_output(self, tx_input: "TxInput") -> Optional["TxOutput"]:
        tx = self.get_tx(tx_input.connected_tx_output_tx_id)
        if tx:
            return tx.tx_outputs[tx_input.connected_tx_output_index]
        return None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TxOutput
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_unordered_tx_output_stream(self):
        return (
            tx_output
            for tx in self.get_unordered_tx_stream()
            for tx_output in tx.tx_outputs
        )

    def exists_tx_output(self, tx_output_key: "TxOutputKey") -> bool:
        return any(
            tx_output.get_key() == tx_output_key
            for tx_output in self.get_unordered_tx_output_stream()
        )

    def get_tx_output(self, tx_output_key: "TxOutputKey") -> Optional["TxOutput"]:
        return next(
            (
                tx_output
                for tx_output in self.get_unordered_tx_output_stream()
                if tx_output.get_key() == tx_output_key
            ),
            None,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // UnspentTxOutput
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_unspent_tx_output_map(self):
        return self.dao_state.unspent_tx_output_map

    def get_spent_info_map(self):
        return self.dao_state.spent_info_map

    def add_unspent_tx_output(self, tx_output: "TxOutput") -> None:
        self._assert_dao_state_change()
        self.get_unspent_tx_output_map()[tx_output.get_key()] = tx_output

    def remove_unspent_tx_output(self, tx_output: "TxOutput") -> None:
        self._assert_dao_state_change()
        self.get_unspent_tx_output_map().pop(tx_output.get_key(), None)

    def is_unspent(self, key: "TxOutputKey") -> bool:
        return key in self.get_unspent_tx_output_map()

    def get_unspent_tx_outputs(self):
        return set(self.get_unspent_tx_output_map().values())

    def get_unspent_tx_output(self, key: "TxOutputKey") -> Optional["TxOutput"]:
        return self.get_unspent_tx_output_map().get(key, None)

    def get_unspent_tx_output_value(self, key: "TxOutputKey") -> int:
        tx_output = self.get_unspent_tx_output(key)
        return tx_output.value if tx_output else 0

    def is_tx_output_key_spendable(self, key: "TxOutputKey") -> bool:
        if not self.is_unspent(key):
            return False

        tx_output = self.get_unspent_tx_output(key)
        check_argument(tx_output is not None, "tx_output must be present")
        return self.is_tx_output_spendable(tx_output)

    def is_tx_output_spendable(self, tx_output: "TxOutput") -> bool:
        # OP_RETURN_OUTPUTs are actually not spendable but as we have no value on them
        # they would not be used anyway.
        tx_output_type = tx_output.tx_output_type
        if tx_output_type == TxOutputType.UNDEFINED_OUTPUT:
            return False
        elif tx_output_type in {
            TxOutputType.GENESIS_OUTPUT,
            TxOutputType.BSQ_OUTPUT,
            TxOutputType.PROPOSAL_OP_RETURN_OUTPUT,
            TxOutputType.COMP_REQ_OP_RETURN_OUTPUT,
            TxOutputType.REIMBURSEMENT_OP_RETURN_OUTPUT,
            TxOutputType.ISSUANCE_CANDIDATE_OUTPUT,
            TxOutputType.BLIND_VOTE_OP_RETURN_OUTPUT,
            TxOutputType.VOTE_REVEAL_UNLOCK_STAKE_OUTPUT,
            TxOutputType.VOTE_REVEAL_OP_RETURN_OUTPUT,
            TxOutputType.LOCKUP_OP_RETURN_OUTPUT,
        }:
            return True
        elif tx_output_type in {
            TxOutputType.BTC_OUTPUT,
            TxOutputType.BLIND_VOTE_LOCK_STAKE_OUTPUT,
            TxOutputType.ASSET_LISTING_FEE_OP_RETURN_OUTPUT,
            TxOutputType.PROOF_OF_BURN_OP_RETURN_OUTPUT,
            TxOutputType.LOCKUP_OUTPUT,
            TxOutputType.INVALID_OUTPUT,
        }:
            return False
        elif tx_output_type == TxOutputType.UNLOCK_OUTPUT:
            return self.is_lock_time_over_for_unlock_tx_output(tx_output)
        else:
            return False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TxOutputType
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx_outputs_by_tx_output_type(
        self, tx_output_type: "TxOutputType"
    ) -> set["TxOutput"]:
        return self.dao_state.get_tx_output_by_tx_output_type(tx_output_type)

    def is_bsq_tx_output_type(self, tx_output: "TxOutput") -> bool:
        tx_output_type = tx_output.tx_output_type
        if tx_output_type == TxOutputType.UNDEFINED_OUTPUT:
            return False
        elif tx_output_type in {
            TxOutputType.GENESIS_OUTPUT,
            TxOutputType.BSQ_OUTPUT,
            TxOutputType.PROPOSAL_OP_RETURN_OUTPUT,
            TxOutputType.COMP_REQ_OP_RETURN_OUTPUT,
            TxOutputType.REIMBURSEMENT_OP_RETURN_OUTPUT,
            TxOutputType.BLIND_VOTE_LOCK_STAKE_OUTPUT,
            TxOutputType.BLIND_VOTE_OP_RETURN_OUTPUT,
            TxOutputType.VOTE_REVEAL_UNLOCK_STAKE_OUTPUT,
            TxOutputType.VOTE_REVEAL_OP_RETURN_OUTPUT,
            TxOutputType.ASSET_LISTING_FEE_OP_RETURN_OUTPUT,
            TxOutputType.PROOF_OF_BURN_OP_RETURN_OUTPUT,
            TxOutputType.LOCKUP_OUTPUT,
            TxOutputType.LOCKUP_OP_RETURN_OUTPUT,
            TxOutputType.UNLOCK_OUTPUT,
        }:
            return True
        elif tx_output_type == TxOutputType.ISSUANCE_CANDIDATE_OUTPUT:
            return self.is_issuance_tx(tx_output.tx_id)
        elif (
            tx_output_type == TxOutputType.BTC_OUTPUT
            or tx_output_type == TxOutputType.INVALID_OUTPUT
        ):
            return False
        else:
            return False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TxOutputType - Voting
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_unspent_blind_vote_stake_tx_outputs(self) -> set["TxOutput"]:
        return {
            tx_output
            for tx_output in self.get_tx_outputs_by_tx_output_type(
                TxOutputType.BLIND_VOTE_LOCK_STAKE_OUTPUT
            )
            if self.is_unspent(tx_output.get_key())
        }

    def get_vote_reveal_op_return_tx_outputs(self) -> set["TxOutput"]:
        return self.get_tx_outputs_by_tx_output_type(
            TxOutputType.VOTE_REVEAL_OP_RETURN_OUTPUT
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // TxOutputType - Issuance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_issuance_candidate_tx_outputs(self) -> set["TxOutput"]:
        return self.get_tx_outputs_by_tx_output_type(
            TxOutputType.ISSUANCE_CANDIDATE_OUTPUT
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Issuance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_issuance(self, issuance: "Issuance") -> None:
        self._assert_dao_state_change()
        self.dao_state.issuance_map[issuance.tx_id] = issuance

    def get_issuance_items(self):
        return self.dao_state.issuance_map.values()

    def get_issuance_set_for_type(
        self, issuance_type: "IssuanceType"
    ) -> set["Issuance"]:
        return {
            issuance
            for issuance in self.get_issuance_items()
            if issuance.issuance_type == issuance_type
        }

    def get_issuance(
        self, tx_id: str, issuance_type: Optional["IssuanceType"] = None
    ) -> Optional["Issuance"]:
        issuance = self.dao_state.issuance_map.get(tx_id, None)
        if issuance and (
            issuance_type is None or issuance.issuance_type == issuance_type
        ):
            return issuance
        return None

    def is_issuance_tx(
        self, tx_id: str, issuance_type: Optional["IssuanceType"] = None
    ) -> bool:
        return self.get_issuance(tx_id, issuance_type) is not None

    def get_issuance_block_height(self, tx_id: str) -> int:
        issuance = self.get_issuance(tx_id)
        return issuance.chain_height if issuance else 0

    def get_total_issued_amount(self, issuance_type: "IssuanceType") -> int:
        return sum(
            tx_output.value
            for tx_output in self.get_issuance_candidate_tx_outputs()
            if self.is_issuance_tx(tx_output.tx_id, issuance_type)
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Not accepted issuance candidate outputs of past cycles
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_rejected_issuance_output(self, tx_output_key: "TxOutputKey") -> bool:
        current_cycle = self.current_cycle
        if current_cycle:
            return any(
                tx_output.get_key() == tx_output_key
                and not current_cycle.is_in_cycle(tx_output.block_height)
                and not self.is_issuance_tx(tx_output.tx_id)
                for tx_output in self.get_issuance_candidate_tx_outputs()
            )
        return False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Bond
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Terminology
    # HashOfBondId - 20 bytes hash of the bond ID
    # Lockup - txOutputs of LOCKUP type
    # Unlocking - UNLOCK txOutputs that are not yet spendable due to lock time
    # Unlocked - UNLOCK txOutputs that are spendable since the lock time has passed
    # LockTime - 0 means that the funds are spendable at the same block of the UNLOCK tx. For the user that is not
    # supported as we do not expose unconfirmed BSQ txs so lockTime of 1 is the smallest the user can actually use.

    # LockTime

    def get_lock_time(self, tx_id: str) -> Optional[int]:
        tx = self.get_tx(tx_id)
        return tx.lock_time if tx else None

    def get_lockup_hash(self, tx_output: "TxOutput") -> Optional[bytes]:
        lockup_tx = None
        tx_id = tx_output.tx_id
        if tx_output.tx_output_type == TxOutputType.LOCKUP_OUTPUT:
            lockup_tx = self.get_tx(tx_id)
        elif self.is_unlock_tx_output_and_lock_time_not_over(tx_output):
            unlock_tx = self.get_tx(tx_id)
            if unlock_tx:
                lockup_tx = self.get_tx(
                    unlock_tx.tx_inputs[0].connected_tx_output_tx_id
                )

        if lockup_tx:
            op_return_data = lockup_tx.last_tx_output.op_return_data
            if op_return_data:
                return BondConsensus.get_hash_from_op_return_data(op_return_data)
        return None

    def is_unlock_tx_output_and_lock_time_not_over(self, tx_output: "TxOutput") -> bool:
        return (
            tx_output.tx_output_type == TxOutputType.UNLOCK_OUTPUT
            and not self.is_lock_time_over_for_unlock_tx_output(tx_output)
        )

    def is_lockup_output(self, key: "TxOutputKey") -> bool:
        tx_output = self.get_unspent_tx_output(key)
        return tx_output is not None and self.is_lockup_output_tx(tx_output)

    def is_lockup_output_tx(self, tx_output: "TxOutput") -> bool:
        return tx_output.tx_output_type == TxOutputType.LOCKUP_OUTPUT

    def get_lockup_tx_outputs(self) -> set["TxOutput"]:
        return self.get_tx_outputs_by_tx_output_type(TxOutputType.LOCKUP_OUTPUT)

    def get_unlock_tx_outputs(self) -> set["TxOutput"]:
        return self.get_tx_outputs_by_tx_output_type(TxOutputType.UNLOCK_OUTPUT)

    def get_unspent_lockup_tx_outputs(self) -> set["TxOutput"]:
        return {
            tx_output
            for tx_output in self.get_tx_outputs_by_tx_output_type(
                TxOutputType.LOCKUP_OUTPUT
            )
            if self.is_unspent(tx_output.get_key())
        }

    def get_lockup_tx_output(self, tx_id: str) -> Optional["TxOutput"]:
        tx = self.get_tx(tx_id)
        if tx:
            return next(
                (
                    tx_output
                    for tx_output in tx.tx_outputs
                    if self.is_lockup_output_tx(tx_output)
                ),
                None,
            )
        return None

    def get_lockup_op_return_tx_output(self, tx_id: str) -> Optional["TxOutput"]:
        tx = self.get_tx(tx_id)
        if tx:
            last_tx_output = tx.last_tx_output
            if last_tx_output.op_return_data is not None:
                return last_tx_output
        return None

    # Returns amount of all LOCKUP txOutputs (they might have been unlocking or unlocked in the meantime)
    def get_total_amount_of_lockup_tx_outputs(self) -> int:
        return sum(
            tx_output.value
            for tx_output in self.get_lockup_tx_outputs()
            if not self.is_confiscated_lockup_tx_output(tx_output.tx_id)
        )

    # Returns the current locked up amount (excluding unlocking and unlocked)
    def get_total_lockup_amount(self) -> int:
        return (
            self.get_total_amount_of_lockup_tx_outputs()
            - self.get_total_amount_of_unlocking_tx_outputs()
            - self.get_total_amount_of_unlocked_tx_outputs()
        )

    def is_unspent_unlock_output(self, key: "TxOutputKey") -> bool:
        tx_output = self.get_unspent_tx_output(key)
        return tx_output is not None and self.is_unlock_output(tx_output)

    def is_unlock_output(self, tx_output: "TxOutput") -> bool:
        return tx_output.tx_output_type == TxOutputType.UNLOCK_OUTPUT

    # Unlocking
    # Return UNLOCK TxOutputs that are not yet spendable as lockTime is not over
    def get_unspent_unlocking_tx_outputs_stream(self):
        return (
            tx_output
            for tx_output in self.get_tx_outputs_by_tx_output_type(
                TxOutputType.UNLOCK_OUTPUT
            )
            if self.is_unspent(tx_output.get_key())
            and not self.is_lock_time_over_for_unlock_tx_output(tx_output)
        )

    def get_total_amount_of_unlocking_tx_outputs(self) -> int:
        return sum(
            tx_output.value
            for tx_output in self.get_unspent_unlocking_tx_outputs_stream()
            if not self.is_confiscated_unlock_tx_output(tx_output.tx_id)
        )

    def is_unlocking_and_unspent_key(self, key: "TxOutputKey") -> bool:
        tx_output = self.get_unspent_tx_output(key)
        return tx_output is not None and self.is_unlocking_and_unspent_tx_output(
            tx_output
        )

    def is_unlocking_and_unspent_tx_id(self, unlock_tx_id: str) -> bool:
        tx = self.get_tx(unlock_tx_id)
        return tx is not None and self.is_unlocking_and_unspent_tx_output(
            tx.tx_outputs[0]
        )

    def is_unlocking_and_unspent_tx_output(self, unlock_tx_output: "TxOutput") -> bool:
        return (
            unlock_tx_output.tx_output_type == TxOutputType.UNLOCK_OUTPUT
            and self.is_unspent(unlock_tx_output.get_key())
            and not self.is_lock_time_over_for_unlock_tx_output(unlock_tx_output)
        )

    def get_lockup_tx_from_unlock_tx_id(self, unlock_tx_id: str) -> Optional["Tx"]:
        unlock_tx = self.get_tx(unlock_tx_id)
        if unlock_tx:
            connected_tx_output_tx_id = unlock_tx.tx_inputs[0].connected_tx_output_tx_id
            return self.get_tx(connected_tx_output_tx_id)
        return None

    def get_unlock_tx_from_lockup_tx_id(self, lockup_tx_id: str) -> Optional["Tx"]:
        lockup_tx = self.get_tx(lockup_tx_id)
        if lockup_tx:
            spent_info = self.get_spent_info(lockup_tx.tx_outputs[0])
            if spent_info:
                return self.get_tx(spent_info.tx_id)
        return None

    def get_unlock_block_height(self, tx_id: str) -> Optional[int]:
        tx = self.get_tx(tx_id)
        return tx.unlock_block_height if tx else None

    def is_lock_time_over_for_unlock_tx_output(
        self, unlock_tx_output: "TxOutput"
    ) -> bool:
        check_argument(
            unlock_tx_output.tx_output_type == TxOutputType.UNLOCK_OUTPUT,
            "tx_output must be of type UNLOCK",
        )
        unlock_block_height = self.get_unlock_block_height(unlock_tx_output.tx_id)
        return unlock_block_height is not None and BondConsensus.is_lock_time_over(
            unlock_block_height, self.chain_height
        )

    # We don't care here about the unspent state
    def get_unlocked_tx_outputs_stream(self):
        return (
            tx_output
            for tx_output in self.get_tx_outputs_by_tx_output_type(
                TxOutputType.UNLOCK_OUTPUT
            )
            if not self.is_confiscated_unlock_tx_output(tx_output.tx_id)
            and self.is_lock_time_over_for_unlock_tx_output(tx_output)
        )

    def get_total_amount_of_unlocked_tx_outputs(self) -> int:
        return sum(
            tx_output.value for tx_output in self.get_unlocked_tx_outputs_stream()
        )

    def get_total_amount_of_confiscated_tx_outputs(self) -> int:
        return sum(
            tx.lockup_output.value
            for tx in (
                self.get_tx(tx_id)
                for tx_id in self.dao_state.confiscated_lockup_tx_list
            )
            if tx is not None
        )

    def get_total_amount_of_invalidated_bsq(self) -> int:
        return sum(tx.invalidated_bsq for tx in self.get_unordered_tx_stream())

    # Contains burnt fee and invalidated bsq due invalid txs
    def get_total_amount_of_burnt_bsq(self) -> int:
        return sum(tx.burnt_bsq for tx in self.get_unordered_tx_stream())

    # Confiscate bond
    def confiscate_bond(self, lockup_tx_id: str) -> None:
        lockup_tx_output = self.get_lockup_tx_output(lockup_tx_id)
        if lockup_tx_output:
            if self.is_unspent(lockup_tx_output.get_key()):
                logger.warning(
                    f"confiscateBond: lockupTxOutput {lockup_tx_output.get_key()} is still unspent so we can confiscate it."
                )
                self._do_confiscate_bond(lockup_tx_id)
            else:
                # We lookup for the unlock tx which need to be still in unlocking state
                spent_info = self.get_spent_info(lockup_tx_output)
                check_argument(spent_info is not None, "spent_info must be present")
                unlock_tx_id = spent_info.tx_id
                if self.is_unlocking_and_unspent_tx_id(unlock_tx_id):
                    # We found the unlock tx is still not spend
                    logger.warning(
                        f"confiscateBond: lockupTxOutput {lockup_tx_output.get_key()} is still unspent so we can confiscate it."
                    )
                    self._do_confiscate_bond(lockup_tx_id)
                else:
                    # We could be more radical here and confiscate the output if it is unspent but lock time is over,
                    # but it's probably better to stick to the rules that confiscation can only happen before lock time
                    # is over.
                    logger.warning(
                        f"We could not confiscate the bond because the unlock tx was already spent or lock time has exceeded. unlockTxId={unlock_tx_id}"
                    )
        else:
            logger.warning(f"No lockupTxOutput found for lockupTxId {lockup_tx_id}")

    def _do_confiscate_bond(self, lockup_tx_id: str) -> None:
        self._assert_dao_state_change()
        logger.warning(f"TxId {lockup_tx_id} added to confiscatedLockupTxIdList.")
        self.dao_state.confiscated_lockup_tx_list.append(lockup_tx_id)

    def is_confiscated_output(self, tx_output_key: "TxOutputKey") -> bool:
        if self.is_lockup_output(tx_output_key):
            return self.is_confiscated_lockup_tx_output(tx_output_key.tx_id)
        elif self.is_unspent_unlock_output(tx_output_key):
            return self.is_confiscated_unlock_tx_output(tx_output_key.tx_id)
        return False

    def is_confiscated_lockup_tx_output(self, lockup_tx_id: str) -> bool:
        return lockup_tx_id in self.dao_state.confiscated_lockup_tx_list

    def is_confiscated_unlock_tx_output(self, unlock_tx_id: str) -> bool:
        lockup_tx = self.get_lockup_tx_from_unlock_tx_id(unlock_tx_id)
        return lockup_tx is not None and self.is_confiscated_lockup_tx_output(
            lockup_tx.id
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Param
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def set_new_param(
        self, block_height: int, param: "Param", param_value: str
    ) -> None:
        self._assert_dao_state_change()
        param_change_list = self.dao_state.param_change_list
        next_cycle_start_height = self.get_start_height_of_next_cycle(block_height)
        if next_cycle_start_height is not None:
            param_change = ParamChange(param.name, param_value, next_cycle_start_height)
            param_change_list.append(param_change)
            # Addition with older height should not be possible but to ensure correct sorting lets run a sort.
            param_change_list.sort(key=lambda pc: pc.activation_height)

    def get_param_value(self, param: "Param", block_height: int):
        param_change_list = list(self.dao_state.param_change_list)
        if param_change_list:
            # List is sorted by height, we start from latest entries to find most recent entry.
            for param_change in reversed(param_change_list):
                if (
                    param_change.param_name == param.name
                    and block_height >= param_change.activation_height
                ):
                    return param_change.value

        # If no value found we use default values
        return param.default_value

    def get_param_change_list(self, param: "Param"):
        values = list[Coin]()
        for param_change in self.dao_state.param_change_list:
            if param_change.param_name == param.name:
                values.append(self.get_param_value_as_coin(param, param_change.value))
        return values

    def get_param_value_as_coin(
        self, param: "Param", block_height_or_param_value: Union[int, str]
    ):
        if isinstance(block_height_or_param_value, int):
            block_height_or_param_value = self.get_param_value(
                param, block_height_or_param_value
            )
        return self.bsq_formatter.parse_param_value_to_coin(
            param, block_height_or_param_value
        )

    def get_param_value_as_percent_double(
        self, param_or_value: Union[str, "Param"], block_height: int = None
    ) -> float:
        if not isinstance(param_or_value, str) and block_height is not None:
            param_or_value = self.get_param_value(param_or_value, block_height)
        return ParsingUtils.parse_percent_string_to_double(param_or_value)

    def get_param_value_as_block(
        self, param_or_value: str, block_height: int = None
    ) -> int:
        if not isinstance(param_or_value, str) and block_height is not None:
            param_or_value = self.get_param_value(param_or_value, block_height)
        return int(param_or_value)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // SpentInfo
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def set_spent_info(
        self, tx_output_key: "TxOutputKey", spent_info: "SpentInfo"
    ) -> None:
        self._assert_dao_state_change()
        self.dao_state.spent_info_map[tx_output_key] = spent_info

    def get_spent_info(self, tx_output: "TxOutput") -> Optional["SpentInfo"]:
        return self.dao_state.spent_info_map.get(tx_output.get_key(), None)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Addresses
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_tx_id_set_by_address(self) -> dict[str, set[str]]:
        # We clear it at each new (non-empty) block, so it gets recreated
        if self._cached_tx_id_set_by_address:
            return self._cached_tx_id_set_by_address

        tx_id_by_connected_tx_output_key: dict["TxOutputKey", str] = {}
        # Add tx ids and addresses from tx outputs
        for tx in self.get_unordered_tx_stream():
            for tx_output in tx.tx_outputs:
                if self.is_bsq_tx_output_type(tx_output) and tx_output.address:
                    address = tx_output.address
                    tx_id_set = self._cached_tx_id_set_by_address.get(address, set())
                    tx_id_set.add(tx.id)
                    self._cached_tx_id_set_by_address[address] = tx_id_set
                    for tx_input in tx.tx_inputs:
                        tx_id_by_connected_tx_output_key[
                            tx_input.get_connected_tx_output_key()
                        ] = tx.id

        # Add tx ids and addresses from connected outputs (inputs)
        for tx_output in self.get_unordered_tx_output_stream():
            if self.is_bsq_tx_output_type(tx_output) and tx_output.address:
                tx_id = tx_id_by_connected_tx_output_key.get(tx_output.get_key())
                if tx_id:
                    address = tx_output.address
                    tx_id_set = self._cached_tx_id_set_by_address.get(address, set())
                    tx_id_set.add(tx_id)
                    self._cached_tx_id_set_by_address[address] = tx_id_set

        return self._cached_tx_id_set_by_address

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Vote result data
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_evaluated_proposal_list(self) -> list["EvaluatedProposal"]:
        return self.dao_state.evaluated_proposal_list

    def add_evaluated_proposal_set(
        self, evaluated_proposals: set["EvaluatedProposal"]
    ) -> None:
        self._assert_dao_state_change()

        for proposal in evaluated_proposals:
            if proposal not in self.dao_state.evaluated_proposal_list:
                self.dao_state.evaluated_proposal_list.append(proposal)

        # We need deterministic order for the hash chain
        self.dao_state.evaluated_proposal_list.sort(key=lambda e: e.proposal_tx_id)

    def get_decrypted_ballots_with_merits_list(
        self,
    ) -> list["DecryptedBallotsWithMerits"]:
        return self.dao_state.decrypted_ballots_with_merits_list

    def add_decrypted_ballots_with_merits_set(
        self, decrypted_ballots_with_merits_set: set["DecryptedBallotsWithMerits"]
    ) -> None:
        self._assert_dao_state_change()

        for ballot in decrypted_ballots_with_merits_set:
            if ballot not in self.dao_state.decrypted_ballots_with_merits_list:
                self.dao_state.decrypted_ballots_with_merits_list.append(ballot)

        # We need deterministic order for the hash chain
        self.dao_state.decrypted_ballots_with_merits_list.sort(
            key=lambda e: e.blind_vote_tx_id
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Asset listing fee
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_asset_listing_fee_op_return_tx_outputs(self) -> set["TxOutput"]:
        return self.get_tx_outputs_by_tx_output_type(
            TxOutputType.ASSET_LISTING_FEE_OP_RETURN_OUTPUT
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Proof of burn
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_proof_of_burn_op_return_tx_outputs(self) -> set["TxOutput"]:
        return self.get_tx_outputs_by_tx_output_type(
            TxOutputType.PROOF_OF_BURN_OP_RETURN_OUTPUT
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Listeners
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_dao_state_listener(self, listener: "DaoStateListener") -> None:
        self.dao_state_listeners.add(listener)

    def remove_dao_state_listener(self, listener: "DaoStateListener") -> None:
        self.dao_state_listeners.discard(listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _assert_dao_state_change(self):
        if not self.allow_dao_state_change:
            raise RuntimeError(
                "We got a call which would change the daoState outside of the allowed event phase"
            )
