import contextvars
from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional
from bisq.common.user_thread import UserThread
from bisq.core.dao.burningman.accounting.exceptions.block_hash_not_connecting_exception import (
    BlockHashNotConnectingException,
)
from bisq.core.dao.burningman.accounting.exceptions.block_height_not_connecting_exception import (
    BlockHeightNotConnectingException,
)
from bisq.core.dao.burningman.accounting.node.accounting_node import AccountingNode
import threading
from bisq.core.network.p2p.network.connection_state import ConnectionState
from utils.data import SimplePropertyChangeEvent
from utils.time import get_time_ms
from bisq.core.dao.burningman.accounting.node.lite.network.accounting_lite_network_service import (
    AccountingLiteNodeNetworkService,
)

if TYPE_CHECKING:
    from bisq.core.dao.burningman.accounting.node.messages.get_accounting_blocks_response import (
        GetAccountingBlocksResponse,
    )
    from bisq.core.dao.burningman.accounting.node.messages.new_accounting_block_broadcast_message import (
        NewAccountingBlockBroadcastMessage,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.common.timer import Timer
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bitcoinj.core.block import Block as BitcoinJBlock
    from bisq.core.dao.burningman.burning_man_accounting_service import (
        BurningManAccountingService,
    )
    from bisq.core.user.preferences import Preferences
    from bisq.core.dao.burningman.accounting.node.full.accounting_block_parser import (
        AccountingBlockParser,
    )
    from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
        AccountingBlock,
    )


class AccountingLiteNode(AccountingNode, AccountingLiteNodeNetworkService.Listener):
    """
    Main class for lite nodes which receive the BSQ transactions from a full node (e.g. seed nodes).
    Verification of BSQ transactions is done also by the lite node.
    """

    CHECK_FOR_BLOCK_RECEIVED_DELAY_SEC = 10

    def __init__(
        self,
        p2p_service: "P2PService",
        dao_state_service: "DaoStateService",
        burning_man_accounting_service: "BurningManAccountingService",
        accounting_block_parser: "AccountingBlockParser",
        wallets_setup: "WalletsSetup",
        bsq_wallet_service: "BsqWalletService",
        accounting_lite_node_network_service: "AccountingLiteNodeNetworkService",
        preferences: "Preferences",
        use_dev_privilege_keys: bool,
    ):
        super().__init__(
            p2p_service,
            dao_state_service,
            burning_man_accounting_service,
            accounting_block_parser,
            preferences,
        )
        self.logger = get_ctx_logger(__name__)

        self._wallets_setup = wallets_setup
        self._bsq_wallet_service = bsq_wallet_service
        self._accounting_lite_node_network_service = (
            accounting_lite_node_network_service
        )
        self._use_dev_privilege_keys = use_dev_privilege_keys

        def on_new_block_height(e: SimplePropertyChangeEvent[int]):
            # in place of blockDownloadListener
            if e.new_value > 0:
                self._setup_wallet_best_block_listener()

        self._pending_accounting_blocks: list["AccountingBlock"] = []
        self._block_height_listener = on_new_block_height
        self._check_for_block_received_timer: Optional["Timer"] = None
        self._request_blocks_counter = 0

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Public methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def shut_down(self):
        super().shut_down()
        self._accounting_lite_node_network_service.remove_listener(self)
        self._bsq_wallet_service.remove_new_block_height_listener(
            self._block_height_listener
        )
        self._wallets_setup.chain_height_property.remove_listener(
            self._block_height_listener
        )
        self._accounting_lite_node_network_service.shut_down()
        self._block_height_listener = None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // AccountingLiteNodeNetworkService.Listener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_requested_blocks_received(
        self, get_blocks_response: "GetAccountingBlocksResponse"
    ):
        blocks = get_blocks_response.blocks
        if blocks and self.is_valid_pub_key_and_signature(
            AccountingNode.get_sha256_hash(blocks),
            get_blocks_response.pub_key,
            get_blocks_response.signature,
            self._use_dev_privilege_keys,
        ):
            self._process_accounting_blocks(blocks)

    def on_new_block_received(self, message: "NewAccountingBlockBroadcastMessage"):
        accounting_block = message.block
        if self.is_valid_pub_key_and_signature(
            AccountingNode.get_sha256_hash(accounting_block),
            message.pub_key,
            message.signature,
            self._use_dev_privilege_keys,
        ):
            self._process_new_accounting_block(accounting_block)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We start after initial DAO parsing is complete
    def on_initial_dao_block_parsing_complete(self):
        self._accounting_lite_node_network_service.add_listener(self)

        # We wait until the wallet is synced before using it for triggering requests
        if self._wallets_setup.is_download_complete:
            self._setup_wallet_best_block_listener()
        else:
            self._wallets_setup.chain_height_property.add_listener(
                self._block_height_listener
            )

        super().on_initialized()

    def on_p2p_network_ready(self):
        super().on_p2p_network_ready()

        self._accounting_lite_node_network_service.add_listener(self)

        if not self._initial_block_requests_complete:
            self.start_request_blocks()

    def start_request_blocks(self):
        height_of_last_block = (
            self._burning_man_accounting_service.get_block_height_of_last_block()
        )
        if (
            self._wallets_setup.is_download_complete
            and height_of_last_block == self._bsq_wallet_service.get_best_chain_height()
        ):
            self.logger.info(
                f"No block request needed as we have already the most recent block. "
                f"heightOfLastBlock={height_of_last_block}, bsqWalletService.getBestChainHeight()={self._bsq_wallet_service.get_best_chain_height()}"
            )
            self.on_initial_block_requests_complete()
            return

        ConnectionState.increment_expected_initial_data_responses()
        self._accounting_lite_node_network_service.request_blocks(
            height_of_last_block + 1
        )

    def apply_reorg(self):
        self._pending_accounting_blocks.clear()
        self._accounting_lite_node_network_service.reset()
        super().apply_reorg()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _process_accounting_blocks(self, blocks: list["AccountingBlock"]):
        def process_blocks():
            ts = get_time_ms()
            self.logger.info(
                f"We received blocks from height {blocks[0].height} to {blocks[-1].height}"
            )

            requires_reorg = False
            for block in blocks:
                try:
                    self._burning_man_accounting_service.add_block(block)
                except BlockHeightNotConnectingException as e:
                    self.logger.info(
                        f"Height not connecting. This could happen if we received multiple responses and had already applied a previous one. {e}"
                    )
                except BlockHashNotConnectingException as e:
                    self.logger.warning(
                        f"Interrupt loop because a reorg is required. {e}"
                    )
                    requires_reorg = True
                    break

            UserThread.execute(
                lambda: self._handle_post_block_processing(
                    requires_reorg, len(blocks), ts
                )
            )

        ctx = contextvars.copy_context()
        threading.Thread(
            target=ctx.run,
            args=(process_blocks,),
            name="AccountingLiteNode@process_blocks",
        ).start()

    def _handle_post_block_processing(
        self, requires_reorg: bool, blocks_length: int, ts: int
    ):
        if requires_reorg:
            self.apply_reorg()
            return

        height_of_last_block = (
            self._burning_man_accounting_service.get_block_height_of_last_block()
        )
        if (
            self._wallets_setup.is_download_complete
            and height_of_last_block < self._bsq_wallet_service.get_best_chain_height()
        ):
            self._accounting_lite_node_network_service.request_blocks(
                height_of_last_block + 1
            )
        else:
            if not self._initial_block_requests_complete:
                self.on_initial_block_requests_complete()

        # JAVA: 2833 blocks takes about 24 sec
        self.logger.info(
            f"processAccountingBlocksAsync for {blocks_length} blocks took {get_time_ms() - ts} ms"
        )

    def _process_new_accounting_block(self, accounting_block: "AccountingBlock"):
        block_height = accounting_block.height
        self.logger.info(
            f"onNewBlockReceived: accountingBlock at height {block_height}"
        )

        try:
            self._pending_accounting_blocks.remove(accounting_block)
        except:
            pass
        try:
            self._burning_man_accounting_service.add_block(accounting_block)
            self._burning_man_accounting_service.on_new_block_received(accounting_block)

            # After parsing we check if we have pending blocks we might have received earlier but which have been
            # not connecting from the latest height we had. The list is sorted by height
            if self._pending_accounting_blocks:
                # We take only first element after sorting (so it is the accountingBlock with the next height) to avoid that
                # we would repeat calls in recursions in case we would iterate the list.
                self._pending_accounting_blocks.sort(key=lambda block: block.height)
                next_pending = self._pending_accounting_blocks[0]
                if (
                    next_pending.height
                    == self._burning_man_accounting_service.get_block_height_of_last_block()
                    + 1
                ):
                    self._process_new_accounting_block(next_pending)
        except BlockHeightNotConnectingException:
            #  If height of rawDtoBlock is not at expected heightForNextBlock but further in the future we add it to pendingRawDtoBlocks
            height_for_next_block = (
                self._burning_man_accounting_service.get_block_height_of_last_block()
                + 1
            )
            if (
                accounting_block.height > height_for_next_block
                and accounting_block not in self._pending_accounting_blocks
            ):
                self._pending_accounting_blocks.append(accounting_block)
                self.logger.info(
                    f"We received a accountingBlock with a future accountingBlock height. We store it as pending and try to apply it at the next accountingBlock. "
                    f"heightForNextBlock={height_for_next_block}, accountingBlock: height/truncatedHash={accounting_block.height}/{accounting_block.truncated_hash}"
                )

                self._request_blocks_counter += 1
                self.logger.warning(
                    f"We are trying to call requestBlocks with heightForNextBlock {height_for_next_block} after a delay of {self._request_blocks_counter ** 2} min."
                )
                if self._request_blocks_counter <= 5:

                    def retry_request_blocks():
                        self._pending_accounting_blocks.clear()
                        self._accounting_lite_node_network_service.request_blocks(
                            height_for_next_block
                        )

                    UserThread.run_after(
                        retry_request_blocks,
                        timedelta(seconds=self._request_blocks_counter**2 * 60),
                    )
                else:
                    self.logger.warning(
                        f"We tried {self._request_blocks_counter} times to call requestBlocks with heightForNextBlock {height_for_next_block}."
                    )
        except BlockHashNotConnectingException:
            last_block = self._burning_man_accounting_service.get_last_block()
            self.logger.warning(
                f"Block not connecting:\n"
                f"New block height/hash/previousBlockHash={accounting_block.height}/{accounting_block.truncated_hash}/{accounting_block.truncated_previous_block_hash}, "
                f"latest block height/hash={last_block.height if last_block else 'lastBlock not present'}/{last_block.truncated_hash if last_block else 'lastBlock not present'}"
            )
            self.apply_reorg()

    def _setup_wallet_best_block_listener(self):
        self._wallets_setup.chain_height_property.remove_listener(
            self._block_height_listener
        )

        def on_new_block_height(e: SimplePropertyChangeEvent[int]):
            # If we are not completed with initial block requests we return
            if not self._dao_state_service.parse_block_chain_complete:
                return

            if self._check_for_block_received_timer is not None:
                # In case we received a new block before out timer gets called we stop the old timer
                self._check_for_block_received_timer.stop()

            wallet_block_height = e.new_value
            self.logger.info(
                f"New block at height {wallet_block_height} from bsqWalletService"
            )

            # We expect to receive the new BSQ block from the network shortly after BitcoinJ has been aware of it.
            # If we don't receive it we request it manually from seed nodes
            def check_for_block_received():
                height_of_last_block = (
                    self._burning_man_accounting_service.get_block_height_of_last_block()
                )
                if height_of_last_block < wallet_block_height:
                    self.logger.warning(
                        f"We did not receive a block from the network {AccountingLiteNode.CHECK_FOR_BLOCK_RECEIVED_DELAY_SEC} seconds after we saw the new block in BitcoinJ. "
                        f"We request from our seed nodes missing blocks from block height {height_of_last_block + 1}."
                    )
                    self._accounting_lite_node_network_service.request_blocks(
                        height_of_last_block + 1
                    )

            self._check_for_block_received_timer = UserThread.run_after(
                check_for_block_received,
                timedelta(
                    seconds=AccountingLiteNode.CHECK_FOR_BLOCK_RECEIVED_DELAY_SEC
                ),
            )

        self._bsq_wallet_service.add_new_block_height_listener(on_new_block_height)
