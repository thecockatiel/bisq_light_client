from collections.abc import Callable
from datetime import datetime
from threading import RLock
from typing import Optional
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
    AccountingBlock,
)
from collections import deque

from bisq.core.dao.burningman.accounting.exceptions.block_hash_not_connecting_exception import (
    BlockHashNotConnectingException,
)
from bisq.core.dao.burningman.accounting.exceptions.block_height_not_connecting_exception import (
    BlockHeightNotConnectingException,
)
from bisq.core.dao.burningman.burning_man_accounting_service import (
    BurningManAccountingService,
)
import pb_pb2 as protobuf

logger = get_logger(__name__)


class BurningManAccountingStore(PersistableEnvelope):

    def __init__(self, blocks: list[AccountingBlock]):
        self._lock = RLock()
        self.blocks = blocks.copy()

    def add_if_new_block(self, new_block: AccountingBlock):
        with self._lock:
            self._try_to_add_new_block(new_block)

    def for_each_block(self, consumer: Callable[[AccountingBlock], None]):
        with self._lock:
            for block in self.blocks:
                consumer(block)

    def purge_last_ten_blocks(self):
        with self._lock:
            for _ in range(10):
                if not self.blocks:
                    break
                self.blocks.pop()

    def remove_all_blocks(self):
        with self._lock:
            self.blocks.clear()

    def get_last_block(self) -> Optional[AccountingBlock]:
        with self._lock:
            if not self.blocks:
                return None
            return max(self.blocks, key=lambda block: block.height)

    def get_block_at_height(self, height: int) -> Optional[AccountingBlock]:
        with self._lock:
            return next(
                (block for block in self.blocks if block.height == height), None
            )

    def get_blocks_at_least_with_height(self, min_height: int) -> list[AccountingBlock]:
        with self._lock:
            return [block for block in self.blocks if block.height >= min_height]

    def _try_to_add_new_block(self, new_block: AccountingBlock):
        with self._lock:
            if new_block not in self.blocks:
                last_block = self.get_last_block()
                if last_block:
                    if new_block.height != last_block.height + 1:
                        raise BlockHeightNotConnectingException()
                    if (
                        new_block.truncated_previous_block_hash
                        != last_block.truncated_hash
                    ):
                        raise BlockHashNotConnectingException()
                elif (
                    new_block.height
                    != BurningManAccountingService.EARLIEST_BLOCK_HEIGHT
                ):
                    raise BlockHeightNotConnectingException()
                logger.info(
                    f"Add new accountingBlock at height {new_block.height} at {datetime.fromtimestamp(new_block.time_in_sec)} with {len(new_block.txs)} txs"
                )
                self.blocks.append(new_block)
            else:
                logger.info(f"We have that block already. Height: {new_block.height}")

    def to_proto_message(self):
        with self._lock:
            blocks_copy = self.blocks.copy()
        return protobuf.PersistableEnvelope(
            burning_man_accounting_store=protobuf.BurningManAccountingStore(
                blocks=[block.to_proto_message() for block in blocks_copy]
            )
        )

    @staticmethod
    def from_proto(
        proto: protobuf.BurningManAccountingStore,
    ) -> "BurningManAccountingStore":
        return BurningManAccountingStore(
            blocks=[AccountingBlock.from_proto(block) for block in proto.blocks]
        )
