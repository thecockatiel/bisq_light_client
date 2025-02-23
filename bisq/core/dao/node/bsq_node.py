from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.node.parser.exceptions.block_hash_not_connecting_exception import (
    BlockHashNotConnectingException,
)
from bisq.core.dao.node.parser.exceptions.block_height_not_connecting_exception import (
    BlockHeightNotConnectingException,
)
from bisq.core.dao.node.parser.exceptions.required_reorg_from_snapshot_exception import (
    RequiredReorgFromSnapshotException,
)
from bisq.core.network.p2p.p2p_service_listener import P2PServiceListener
from utils.concurrency import AtomicBoolean

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.node.explorer.export_json_file_manager import (
        ExportJsonFilesService,
    )
    from bisq.core.dao.node.full.raw_block import RawBlock
    from bisq.core.dao.node.parser.block_parser import BlockParser
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.dao_state_snapshot_service import DaoStateSnapshotService
    from bisq.core.network.p2p.p2p_service import P2PService


logger = get_logger(__name__)


class BsqNode(DaoSetupService, ABC):
    """
    Base class for the lite and full node.
    It is responsible or the setup of the parser and snapshot management.
    """

    def __init__(
        self,
        block_parser: "BlockParser",
        dao_state_service: "DaoStateService",
        dao_state_snapshot_service: "DaoStateSnapshotService",
        p2p_service: "P2PService",
        export_json_files_service: "ExportJsonFilesService",
    ):
        self._block_parser = block_parser
        self._dao_state_service = dao_state_service
        self._dao_state_snapshot_service = dao_state_snapshot_service
        self._p2p_service = p2p_service
        self._export_json_files_service = export_json_files_service

        self._genesis_tx_id = dao_state_service.genesis_tx_id
        self._genesis_block_height = dao_state_service.genesis_block_height

        class Listener(P2PServiceListener):
            def on_tor_node_ready(self):
                pass

            def on_hidden_service_published(self):
                pass

            def on_setup_failed(self, throwable):
                pass

            def on_request_custom_bridges(self):
                pass

            def on_data_received(self_):
                self.on_p2p_network_ready()

            def on_no_seed_node_available(self_):
                self.on_p2p_network_ready()

            def on_no_peers_available(self):
                pass

            def on_updated_data_received(self):
                pass

        self.p2p_service_listener: "P2PServiceListener" = Listener()

        self._parse_blockchain_complete = False
        self._p2p_network_ready = False
        self.error_message_handler: Optional[Callable[[str], None]] = None
        self.warn_message_handler: Optional[Callable[[str], None]] = None
        self.pending_blocks: list["RawBlock"] = []

        # The chain height of the latest Block we either get reported by Bitcoin Core or from the seed node
        # This property should not be used in consensus code but only for retrieving blocks as it is not in sync with the
        # parsing and the daoState. It also does not represent the latest blockHeight but the currently received
        # (not parsed) block.
        self.chain_tip_height = 0
        self._shutdown_in_progress = AtomicBoolean(False)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        pass

    @abstractmethod
    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def shut_down(self):
        self._shutdown_in_progress.set(True)
        self._export_json_files_service.shut_down()
        self._dao_state_snapshot_service.shut_down()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_initialized(self):
        self._dao_state_snapshot_service.apply_persisted_snapshot()

        if self._p2p_service.is_bootstrapped:
            logger.info("onAllServicesInitialized: isBootstrapped")
            self.on_p2p_network_ready()
        else:
            self._p2p_service.add_p2p_service_listener(self.p2p_service_listener)

    def on_p2p_network_ready(self):
        self._p2p_network_ready = True
        self._p2p_service.remove_p2p_service_listener(self.p2p_service_listener)

    @abstractmethod
    def start_parse_blocks(self):
        pass

    def on_parse_block_chain_complete(self):
        logger.info("onParseBlockChainComplete")
        self._parse_blockchain_complete = True
        self._dao_state_service.on_parse_block_chain_complete()

        self.maybe_export_to_json()

    def do_parse_block(self, raw_block: "RawBlock") -> Optional["Block"]:
        if self._shutdown_in_progress.get():
            return None

        # We check if we have a block with that height. If so we return. We do not use the chainHeight as with genesis
        # height we have no block but chainHeight is initially set to genesis height (bad design ;-( but a bit tricky
        # to change now as it used in many areas.)
        if self._dao_state_service.get_block_at_height(raw_block.height):
            logger.info(
                f"We have already a block with the height of the new block. Height of new block={raw_block.height}"
            )
            return None

        try:
            block = self._block_parser.parse_block(raw_block)

            self.pending_blocks.remove(raw_block)

            # After parsing we check if we have pending blocks we might have received earlier but which have been
            # not connecting from the latest height we had. The list is sorted by height
            if self.pending_blocks:
                # We take only first element after sorting (so it is the block with the next height) to avoid that
                # we would repeat calls in recursions in case we would iterate the list.
                self.pending_blocks.sort(key=lambda b: b.height)
                next_pending = self.pending_blocks[0]
                if next_pending.height == self._dao_state_service.chain_height + 1:
                    self.do_parse_block(next_pending)

            return block
        except BlockHeightNotConnectingException:
            # There is no guaranteed order how we receive blocks. We could have received block 102 before 101.
            # If block is in the future we move the block to the pendingBlocks list. At next block we look up the
            # list if there is any potential candidate with the correct height and if so we remove that from that list.

            height_for_next_block = self._dao_state_service.chain_height + 1
            if raw_block.height > height_for_next_block:
                # rawBlock is not at expected next height but further in the future
                if raw_block not in self.pending_blocks:
                    self.pending_blocks.append(raw_block)
                    logger.info(
                        f"We received a block with a future block height. We store it as pending and try to apply it at the next block. rawBlock: height/hash={raw_block.height}/{raw_block.hash}"
                    )
                else:
                    logger.warning(
                        "We received a block with a future block height but we had it already added to our pendingBlocks."
                    )
            elif raw_block.height >= self._dao_state_service.genesis_block_height:
                # rawBlock is not expected next height but either same height as chainHead or in the past
                # We received an older block. We compare if we have it in our chain.
                existing_block = self._dao_state_service.get_block_at_height(
                    raw_block.height
                )
                if existing_block:
                    if existing_block.hash == raw_block.hash:
                        logger.info(
                            "We received an old block we have already parsed and added. We ignore it."
                        )
                    else:
                        logger.info(
                            f"We received an old block with a different hash. We ignore it. Hash={raw_block.hash}"
                        )
                else:
                    logger.info(
                        "In case we have reset from genesis height we would not find the existingBlockAsSameHeight"
                    )
            else:
                logger.info("We ignore it as it was before genesis height")
        except BlockHashNotConnectingException:
            last_block = self._dao_state_service.last_block
            logger.warning(
                f"Block not connecting:\n"
                f"New block height/hash/previousBlockHash="
                f"{raw_block.height}/{raw_block.hash}/{raw_block.previous_block_hash}, "
                f"latest block height/hash="
                f"{last_block.height if last_block else 'lastBlock not present'}/"
                f"{last_block.hash if last_block else 'lastBlock not present'}"
            )

            self.pending_blocks.clear()
            self._dao_state_snapshot_service.revert_to_last_snapshot()
            self.start_parse_blocks()
            raise RequiredReorgFromSnapshotException(raw_block)

        return None

    def maybe_export_to_json(self):
        self._export_json_files_service.maybe_export_to_json()
