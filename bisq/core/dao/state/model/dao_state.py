from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
import pb_pb2 as protobuf
from bisq.core.dao.state.model.blockchain.tx import Tx
from bisq.core.dao.state.model.blockchain.block import Block
from bisq.core.dao.state.model.blockchain.spent_info import SpentInfo
from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
from bisq.core.dao.state.model.governance.cycle import Cycle
from bisq.core.dao.state.model.governance.decrypted_ballots_with_merits import (
    DecryptedBallotsWithMerits,
)
from bisq.core.dao.state.model.governance.evaluated_proposal import (
    EvaluatedProposal,
)
from bisq.core.dao.state.model.governance.issuance import Issuance
from bisq.core.dao.state.model.governance.param_change import ParamChange


class DaoState(PersistablePayload):
    """
    Root class for mutable state of the DAO.
    Holds both blockchain data as well as data derived from the governance process (voting).

    One BSQ block with empty txs adds 152 bytes which results in about 8 MB/year

    For supporting the hashChain we need to ensure deterministic sorting behaviour of all collections so we use a
    TreeMap which is sorted by the key.
    """

    def __init__(
        self,
        chain_height: int = None,
        blocks: list["Block"] = None,
        cycles: list["Cycle"] = None,
        unspent_tx_output_map: dict["TxOutputKey", "TxOutput"] = None,
        spent_info_map: dict["TxOutputKey", "SpentInfo"] = None,
        confiscated_lockup_tx_list: list[str] = None,
        issuance_map: dict[str, Issuance] = None,
        param_change_list: list["ParamChange"] = None,
        evaluated_proposal_list: list["EvaluatedProposal"] = None,
        decrypted_ballots_with_merits_list: list["DecryptedBallotsWithMerits"] = None,
    ):
        # Is set initially to genesis height
        self.chain_height = chain_height or 0

        # We override the getter so callers can't modify the list without also updating
        # the block caches and indices below
        self._blocks = blocks or []
        self.cycles = cycles or []

        # These maps represent mutual data which can get changed at parsing a transaction
        # We use TreeMaps instead of HashMaps because we need deterministic sorting of the maps for the hashChains
        # used for the DAO monitor.
        self.unspent_tx_output_map = unspent_tx_output_map or {}
        self.spent_info_map = spent_info_map or {}

        # These maps are related to state change triggered by voting
        self.confiscated_lockup_tx_list = confiscated_lockup_tx_list or []
        self.issuance_map = issuance_map or {}  #  key is txId
        self.param_change_list = param_change_list or []

        # Vote result data
        # All evaluated proposals which get added at the result phase
        self.evaluated_proposal_list = evaluated_proposal_list or []
        # All voting data which get added at the result phase
        self.decrypted_ballots_with_merits_list = (
            decrypted_ballots_with_merits_list or []
        )

        # Transient data used only as an index - must be kept in sync with the block list
        self.tx_cache: dict[str, "Tx"] = {
            # key is txId
            # transient JsonExclude
        }
        self.blocks_by_height: dict[int, "Block"] = {
            # transient JsonExclude
            block.height: block
            for block in self._blocks
        }
        self.tx_outputs_by_tx_output_type: dict["TxOutputType", set["TxOutput"]] = (
            {}  # transient JsonExclude
        )

        for block in self._blocks:
            for tx in block._txs:
                self._add_to_tx_outputs_by_tx_output_type_map(tx)
                self.tx_cache[tx.id] = tx

    @property
    def blocks(self):
        """do not modify the list directly, use add_block() instead"""
        return self._blocks

    def _add_to_tx_outputs_by_tx_output_type_map(self, tx: "Tx"):
        for tx_output in tx.tx_outputs:
            if tx_output.tx_output_type not in self.tx_outputs_by_tx_output_type:
                self.tx_outputs_by_tx_output_type[tx_output.tx_output_type] = set()
            self.tx_outputs_by_tx_output_type[tx_output.tx_output_type].add(tx_output)

    def to_proto_message(self) -> protobuf.DaoState:
        builder = self._get_bsq_state_builder_excluding_blocks()
        builder.blocks.extend([block.to_proto_message() for block in self._blocks])
        return builder

    def _get_bsq_state_builder_excluding_blocks(self) -> protobuf.DaoState:
        builder = protobuf.DaoState(
            chain_height=self.chain_height,
            cycles=[cycle.to_proto_message() for cycle in self.cycles],
            unspent_tx_output_map={
                str(key): value.to_proto_message()
                for key, value in self.unspent_tx_output_map.items()
            },
            spent_info_map={
                str(key): value.to_proto_message()
                for key, value in self.spent_info_map.items()
            },
            confiscated_lockup_tx_list=self.confiscated_lockup_tx_list,
            issuance_map={
                key: value.to_proto_message()
                for key, value in self.issuance_map.items()
            },
            param_change_list=[
                param_change.to_proto_message()
                for param_change in self.param_change_list
            ],
            evaluated_proposal_list=[
                proposal.to_proto_message() for proposal in self.evaluated_proposal_list
            ],
            decrypted_ballots_with_merits_list=[
                ballot.to_proto_message()
                for ballot in self.decrypted_ballots_with_merits_list
            ],
        )
        return builder

    @staticmethod
    def from_proto(
        proto: protobuf.DaoState, blocks: list["Block"] = None
    ) -> "DaoState":
        if blocks is None:
            blocks = [Block.from_proto(block_proto) for block_proto in proto.blocks]
        return DaoState(
            chain_height=proto.chain_height,
            blocks=blocks,
            cycles=[Cycle.from_proto(cycle_proto) for cycle_proto in proto.cycles],
            unspent_tx_output_map={
                TxOutputKey.get_key_from_string(key): TxOutput.from_proto(value)
                for key, value in proto.unspent_tx_output_map.items()
            },
            spent_info_map={
                TxOutputKey.get_key_from_string(key): SpentInfo.from_proto(value)
                for key, value in proto.spent_info_map.items()
            },
            confiscated_lockup_tx_list=list(proto.confiscated_lockup_tx_list),
            issuance_map={
                key: Issuance.from_proto(value)
                for key, value in proto.issuance_map.items()
            },
            param_change_list=[
                ParamChange.from_proto(param_change_proto)
                for param_change_proto in proto.param_change_list
            ],
            evaluated_proposal_list=[
                EvaluatedProposal.from_proto(proposal_proto)
                for proposal_proto in proto.evaluated_proposal_list
            ],
            decrypted_ballots_with_merits_list=[
                DecryptedBallotsWithMerits.from_proto(ballot_proto)
                for ballot_proto in proto.decrypted_ballots_with_merits_list
            ],
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Static
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def get_clone(dao_state: "DaoState") -> "DaoState":
        return DaoState.from_proto(dao_state.to_proto_message())

    @staticmethod
    def get_bsq_state_clone_excluding_blocks(
        dao_state: "DaoState",
    ) -> protobuf.DaoState:
        return dao_state._get_bsq_state_builder_excluding_blocks()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_serialized_state_for_hash_chain(self) -> bytes:
        # We only add the last block as for the hash chain we include the prev. hash in the new hash so the state of the
        # earlier blocks is included in the hash. The past blocks cannot be changed anyway when a new block arrives.
        # Reorgs are handled by rebuilding the hash chain from the last snapshot.
        # Using the full blocks list becomes quite heavy. 7000 blocks are
        # about 1.4 MB and creating the hash takes 30 sec. By using just the last block we reduce the time to 7 sec.
        builder = self._get_bsq_state_builder_excluding_blocks()
        if self._blocks:
            builder.blocks.append(self.last_block.to_proto_message())
        return builder.SerializeToString()

    def add_to_tx_cache(self, tx: "Tx"):
        # We shouldn't get duplicate txIds, but use setdefault instead of put for consistency with the map merge
        # function used in the constructor to initialize tx_cache (and to exactly match the pre-caching behavior).
        self.tx_cache.setdefault(tx.id, tx)

        self._add_to_tx_outputs_by_tx_output_type_map(tx)

    def set_tx_cache(self, tx_cache: dict[str, "Tx"]):
        self.tx_cache.clear()
        self.tx_cache.update(tx_cache)

        self.tx_outputs_by_tx_output_type.clear()
        for tx in self.tx_cache.values():
            self._add_to_tx_outputs_by_tx_output_type_map(tx)

    def get_tx_output_by_tx_output_type(
        self, tx_output_type: TxOutputType
    ) -> set["TxOutput"]:
        if tx_output_type in self.tx_outputs_by_tx_output_type:
            return set(self.tx_outputs_by_tx_output_type[tx_output_type])
        else:
            return set()

    @property
    def last_block(self) -> "Block":
        return self._blocks[-1]

    def add_block(self, block: "Block"):
        # The block added here does not have any tx, 
        # so we do not need to update the tx_cache or tx_outputs_by_tx_output_type
        self._blocks.append(block)
        self.blocks_by_height[block.height] = block

    def add_blocks(self, new_blocks: list["Block"]):
        for block in new_blocks:
            self.add_block(block)

    def clear_and_set_blocks(self, new_blocks: list["Block"]):
        """Clears the existing block list and caches, and repopulates them with the new list"""
        self._blocks.clear()
        self.blocks_by_height.clear()

        self.add_blocks(new_blocks)

    def __str__(self):
        return (
            f"DaoState{{\n"
            f"     chainHeight={self.chain_height},\n"
            f"     blocks={self.blocks},\n"
            f"     cycles={self.cycles},\n"
            f"     unspentTxOutputMap={self.unspent_tx_output_map},\n"
            f"     spentInfoMap={self.spent_info_map},\n"
            f"     confiscatedLockupTxList={self.confiscated_lockup_tx_list},\n"
            f"     issuanceMap={self.issuance_map},\n"
            f"     paramChangeList={self.param_change_list},\n"
            f"     evaluatedProposalList={self.evaluated_proposal_list},\n"
            f"     decryptedBallotsWithMeritsList={self.decrypted_ballots_with_merits_list},\n"
            # f"     txCache={self.tx_cache},\n"
            # f"     txOutputsByTxOutputType={self.tx_outputs_by_tx_output_type}\n"
            f"}}"
        )
