from typing import TYPE_CHECKING
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.node.parser.exceptions.block_hash_not_connecting_exception import (
    BlockHashNotConnectingException,
)
from bisq.core.dao.node.parser.exceptions.block_height_not_connecting_exception import (
    BlockHeightNotConnectingException,
)
from bisq.core.dao.state.model.blockchain.block import Block
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.node.full.raw_block import RawBlock
    from bisq.core.dao.node.parser.tx_parser import TxParser
    from bisq.core.dao.state.dao_state_service import DaoStateService


logger = get_logger(__name__)


class BlockParser:
    """
    Parse a rawBlock and creates a block from it with an empty tx list.
    Iterates all rawTx and if the tx is a BSQ tx it gets added to the tx list.
    """

    def __init__(self, tx_parser: "TxParser", dao_state_service: "DaoStateService"):
        self._tx_parser = tx_parser
        self._dao_state_service = dao_state_service
        self._genesis_tx_id = dao_state_service.get_genesis_tx_id()
        self._genesis_block_height = dao_state_service.get_genesis_block_height()
        self._genesis_total_supply = dao_state_service.get_genesis_total_supply()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def parse_block(self, raw_block: "RawBlock") -> Block:
        start_ts = get_time_ms()
        block_height = raw_block.height
        logger.trace(f"Parse block at height={block_height}")

        self._validate_if_block_is_connecting(raw_block)

        self._dao_state_service.on_new_block_height(block_height)

        # We create a block from the rawBlock but the transaction list is not set yet (is empty)
        block = Block(
            block_height,
            raw_block.time,
            raw_block.hash,
            raw_block.previous_block_hash,
        )

        if self._is_block_already_added(raw_block):
            logger.warning("Block was already added.")
            DevEnv.log_error_and_throw_if_dev_mode(
                f"Block was already added. rawBlock={raw_block}"
            )
        else:
            self._dao_state_service.on_new_block_with_empty_txs(block)

        # Worst case is that all txs in a block are depending on another, so only one get resolved at each iteration.
        # Min tx size is 189 bytes (normally about 240 bytes), 1 MB can contain max. about 5300 txs (usually 2000).
        # Realistically we don't expect more than a few recursive calls.
        # There are some blocks with testing such dependency chains like block 130768 where at each iteration only
        # one get resolved.
        # Lately there is a patter with 24 iterations observed

        for raw_tx in raw_block.raw_txs:
            tx = self._tx_parser.find_tx(
                raw_tx,
                self._genesis_tx_id,
                self._genesis_block_height,
                self._genesis_total_supply,
            )
            if tx:
                self._dao_state_service.on_new_tx_for_last_block(block, tx)

        self._dao_state_service.on_parse_block_complete(block)
        duration = get_time_ms() - start_ts
        if duration > 10:
            logger.info(
                f"Parsing {len(raw_block.raw_txs)} transactions at block height {block_height} took {duration} ms"
            )

        return block

    def _validate_if_block_is_connecting(self, raw_block: "RawBlock") -> None:
        blocks = self._dao_state_service.blocks

        if not blocks:
            return

        if self._dao_state_service.block_height_of_last_block + 1 != raw_block.height:
            raise BlockHeightNotConnectingException(raw_block)

        if (
            self._dao_state_service.block_hash_of_last_block
            != raw_block.previous_block_hash
        ):
            raise BlockHashNotConnectingException(raw_block)

    def _is_block_already_added(self, raw_block: "RawBlock") -> bool:
        block = self._dao_state_service.get_block_at_height(raw_block.height)
        if block is not None:
            return block.hash == raw_block.hash
        return False
