from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.dao.node.bsq_node import BsqNode
from bisq.core.dao.node.messages.new_block_broadcast_message import (
    NewBlockBroadcastMessage,
)
from bisq.core.dao.node.parser.exceptions.required_reorg_from_snapshot_exception import (
    RequiredReorgFromSnapshotException,
)
from bisq.core.network.p2p.network.connection_state import ConnectionState
from utils.data import SimplePropertyChangeEvent
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.dao.node.lite.network.lite_node_network_service import (
        LiteNodeNetworkService,
    )
    from bisq.core.dao.node.messages.get_blocks_response import GetBlocksResponse
    from bisq.core.dao.node.full.raw_block import RawBlock
    from bisq.core.dao.node.explorer.export_json_file_manager import (
        ExportJsonFilesService,
    )
    from bisq.core.dao.node.parser.block_parser import BlockParser
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.dao_state_snapshot_service import DaoStateSnapshotService
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.common.timer import Timer
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bitcoinj.core.block import Block as BitcoinJBlock


logger = get_logger(__name__)


class LiteNode(BsqNode):
    """
    Main class for lite nodes which receive the BSQ transactions from a full node (e.g. seed nodes).
    Verification of BSQ transactions is done also by the lite node.
    """

    CHECK_FOR_BLOCK_RECEIVED_DELAY_SEC = 10

    def __init__(
        self,
        block_parser: "BlockParser",
        dao_state_service: "DaoStateService",
        dao_state_snapshot_service: "DaoStateSnapshotService",
        p2p_service: "P2PService",
        lite_node_network_service: "LiteNodeNetworkService",
        bsq_wallet_service: "BsqWalletService",
        wallets_setup: "WalletsSetup",
        export_json_files_service: ExportJsonFilesService,
    ):
        super().__init__(
            block_parser,
            dao_state_service,
            dao_state_snapshot_service,
            p2p_service,
            export_json_files_service,
        )

        self._lite_node_network_service = lite_node_network_service
        self._bsq_wallet_service = bsq_wallet_service
        self._wallets_setup = wallets_setup

        self._check_for_block_received_timer: Optional["Timer"] = None

        def block_download_listener(e: SimplePropertyChangeEvent["float"]):
            if e.new_value == 1:
                self._setup_wallet_best_block_listener()
                self._maybe_start_requesting_blocks()

        self._block_download_listener = block_download_listener

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Public methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def start(self):
        super().on_initialized()

        self._lite_node_network_service.start()

        # We wait until the wallet is synced before using it for triggering requests
        if self._wallets_setup.is_download_complete:
            self._setup_wallet_best_block_listener()
        else:
            self._wallets_setup.download_percentage_property.add_listener(
                self._block_download_listener
            )

    def _setup_wallet_best_block_listener(self):
        self._wallets_setup.download_percentage_property.remove_listener(
            self._block_download_listener
        )

        def on_new_best_block(block_from_wallet: "BitcoinJBlock"):
            # Check if we are done with parsing
            if not self._dao_state_service.parse_block_chain_complete:
                return

            if self._check_for_block_received_timer is not None:
                # In case we received a new block before out timer gets called we stop the old timer
                self._check_for_block_received_timer.stop()

            wallet_block_height = block_from_wallet.height
            logger.info(
                f"New block at height {wallet_block_height} from bsqWalletService"
            )

            # We expect to receive the new BSQ block from the network shortly after BitcoinJ has been aware of it.
            # If we don't receive it we request it manually from seed nodes
            def check_for_block_received():
                dao_chain_height = self._dao_state_service.chain_height
                if dao_chain_height < wallet_block_height:
                    logger.warning(
                        f"We did not receive a block from the network {LiteNode.CHECK_FOR_BLOCK_RECEIVED_DELAY_SEC} seconds after we saw the new block in BitcoinJ. "
                        f"We request from our seed nodes missing blocks from block height {dao_chain_height + 1}."
                    )
                    self._lite_node_network_service.request_blocks(dao_chain_height + 1)

            self._check_for_block_received_timer = UserThread.run_after(
                check_for_block_received,
                timedelta(seconds=LiteNode.CHECK_FOR_BLOCK_RECEIVED_DELAY_SEC),
            )

        self._bsq_wallet_service.add_new_best_block_listener(on_new_best_block)

    def shut_down(self):
        super().shut_down()
        self._lite_node_network_service.shut_down()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_p2p_network_ready(self):
        super().on_p2p_network_ready()

        # TODO:
        class Listener(LiteNodeNetworkService.Listener):
            def on_requested_blocks_received(
                self_,
                get_blocks_response: "GetBlocksResponse",
                on_parsing_complete: Callable[[], None],
            ):
                self._on_requested_blocks_received(
                    list(get_blocks_response.blocks), on_parsing_complete
                )

            def on_new_block_received(
                self_, new_block_broadcast_message: "NewBlockBroadcastMessage"
            ):
                self._on_new_block_received(new_block_broadcast_message.block)

            def on_no_seed_node_available(self_):
                pass

            def on_fault(self_, error_message, connection):
                pass

        self._lite_node_network_service.add_listener(Listener())
        self._maybe_start_requesting_blocks()

    def _maybe_start_requesting_blocks(self):
        if (
            self._wallets_setup.is_download_complete
            and self._p2p_network_ready
            and not self._parse_blockchain_complete
        ):
            self._start_parse_blocks()

    # First we request the blocks from a full node
    def _start_parse_blocks(self):
        chain_height = self._dao_state_service.chain_height
        if (
            self._wallets_setup.is_download_complete
            and chain_height == self._bsq_wallet_service.get_best_chain_height()
        ):
            logger.info(
                "No block request needed as we have already the most recent block. "
                f"daoStateService.getChainHeight()={chain_height}, "
                f"bsqWalletService.getBestChainHeight()={self._bsq_wallet_service.get_best_chain_height()}"
            )
            self.on_parse_block_chain_complete()
            return

        # If we request blocks we increment the ConnectionState counter so that the connection does not get reset from
        # INITIAL_DATA_EXCHANGE to PEER and therefore lower priority for getting closed
        ConnectionState.increment_expected_initial_data_responses()

        if chain_height == self._dao_state_service.genesis_block_height:
            self._lite_node_network_service.request_blocks(chain_height)
        else:
            self._lite_node_network_service.request_blocks(chain_height + 1)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We received the missing blocks
    def _on_requested_blocks_received(
        self, block_list: list["RawBlock"], on_parsing_complete: Callable[[], None]
    ):
        if block_list:
            self.chain_tip_height = block_list[-1].height
            logger.info(
                f"We received blocks from height {block_list[0].height} to {self.chain_tip_height}"
            )

        # We delay the parsing to next render frame to avoid that the UI get blocked in case we parse a lot of blocks.
        # Parsing itself is very fast (3 sec. for 7000 blocks) but creating the hash chain slows down batch processing a lot
        # (30 sec for 7000 blocks).
        # The updates at block height change are not much optimized yet, so that can be for sure improved
        # 144 blocks a day would result in about 4000 in a month, so if a user downloads the app after 1 months latest
        # release it will be a bit of a performance hit. It is a one time event as the snapshots gets created and be
        # used at next startup. New users will get the shipped snapshot. Users who have not used Bisq for longer might
        # experience longer durations for batch processing.
        ts = get_time_ms()

        if not block_list:
            self.on_parse_block_chain_complete()
            return

        if (
            self._wallets_setup.is_download_complete
            and self.chain_tip_height < self._bsq_wallet_service.get_best_chain_height()
        ):
            # We need to request more blocks and increment the ConnectionState counter so that the connection does not get reset from
            # INITIAL_DATA_EXCHANGE to PEER and therefore lower priority for getting closed
            ConnectionState.increment_expected_initial_data_responses()

        # TODO: sanity check: why we make a copy for processing but not for after it ?
        self._run_delayed_batch_processing(
            block_list.copy(),
            lambda: self._on_batch_processing_complete(
                block_list, ts, on_parsing_complete
            ),
        )

    def _on_batch_processing_complete(
        self,
        block_list: list["RawBlock"],
        ts: int,
        on_parsing_complete: Callable[[], None],
    ):
        duration = get_time_ms() - ts
        logger.info(
            f"Parsing {len(block_list)} blocks took {duration / 1000:.2f} seconds "
            f"({duration / 1000 / 60:.2f} min.) / {duration / len(block_list):.2f} ms in average / block"
        )
        # We only request again if wallet is synced, otherwise we would get repeated calls we want to avoid.
        # We deal with that case at the setupWalletBestBlockListener method above.
        if self._wallets_setup.is_download_complete and (
            self._dao_state_service.chain_height
            < self._bsq_wallet_service.get_best_chain_height()
        ):
            logger.info(
                f"We have completed batch processing of {len(block_list)} blocks but we have still "
                f"{self._bsq_wallet_service.get_best_chain_height() - self._dao_state_service.chain_height} missing blocks and request again."
            )
            self._lite_node_network_service.request_blocks(
                self._dao_state_service.chain_height + 1
            )
        else:
            logger.info(
                f"We have completed batch processing of {len(block_list)} blocks and we have reached the chain tip of the wallet."
            )
            on_parsing_complete()
            self.on_parse_block_chain_complete()

    def _run_delayed_batch_processing(
        self, blocks: list["RawBlock"], result_handler: Callable[[], None]
    ):
        if self._shutdown_in_progress:
            return

        def process_next_block():
            if not blocks:
                result_handler()
                return

            block = blocks.pop(0)
            try:
                self.do_parse_block(block)
                self._run_delayed_batch_processing(blocks, result_handler)
            except RequiredReorgFromSnapshotException as e:
                logger.warning(
                    f"doParseBlock failed at runDelayedBatchProcessing because of a blockchain reorg. {e}"
                )

        UserThread.execute(process_next_block)

    #  We received a new block
    def _on_new_block_received(self, block: "RawBlock"):
        block_height = block.height
        logger.info(
            f"onNewBlockReceived: block at height {block_height}, hash={block.hash}. Our DAO chainHeight={self.chain_tip_height}"
        )

        # We only update chainTipHeight if we get a newer block
        if block_height > self.chain_tip_height:
            self.chain_tip_height = block_height

        try:
            self.do_parse_block(block)
        except RequiredReorgFromSnapshotException as e:
            logger.warning(
                f"doParseBlock failed at onNewBlockReceived because of a blockchain reorg. {e}"
            )

        self.maybe_export_to_json()
