from pathlib import Path
from typing import TYPE_CHECKING
from bisq.common.file.file_util import p2p_list_resource_directory, p2p_resource_to_file
from bisq.common.file.resource_not_found_exception import ResourceNotFoundException
import pb_pb2 as protobuf
from bisq.common.setup.log_setup import get_logger
from utils.time import get_time_ms
from bisq.core.dao.state.storage.blocks_persistence import BlocksPersistence
from bisq.core.dao.state.model.blockchain.block import Block


if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistence_proto_resolver import (
        PersistenceProtoResolver,
    )
    from bisq.core.dao.state.genesis_tx_info import GenesisTxInfo

logger = get_logger(__name__)


class BsqBlocksStorageService:
    NAME = "BsqBlocks"

    def __init__(
        self,
        genesis_tx_info: "GenesisTxInfo",
        persistence_proto_resolver: "PersistenceProtoResolver",
        storage_dir: Path,
    ):
        self._genesis_block_height = genesis_tx_info.genesis_block_height
        self._blocks_dir = storage_dir.joinpath(BsqBlocksStorageService.NAME)
        self._blocks_persistence = BlocksPersistence(
            self._blocks_dir, BsqBlocksStorageService.NAME, persistence_proto_resolver
        )
        self._chain_height_of_persisted_blocks = 0

    @property
    def chain_height_of_persisted_blocks(self) -> int:
        return self._chain_height_of_persisted_blocks

    def persist_blocks(self, blocks: list["Block"]):
        ts = get_time_ms()
        protobuf_blocks = [block.to_proto_message() for block in blocks]
        self._blocks_persistence.write_blocks(protobuf_blocks)

        if blocks:
            self._chain_height_of_persisted_blocks = max(
                self._chain_height_of_persisted_blocks,
                self._get_height_of_last_full_bucket(blocks),
            )
        logger.info(
            f"Persist (serialize+write) {len(blocks)} blocks took {get_time_ms() - ts} ms"
        )

    def read_blocks(self, chain_height: int) -> list["Block"]:
        ts = get_time_ms()
        blocks = []
        protobuf_blocks = self._blocks_persistence.read_blocks(
            self._genesis_block_height, chain_height
        )
        for protobuf_block in protobuf_blocks:
            blocks.append(Block.from_proto(protobuf_block))
        logger.info(
            f"Reading and deserializing {len(blocks)} blocks took {get_time_ms() - ts} ms"
        )
        if blocks:
            self._chain_height_of_persisted_blocks = (
                self._get_height_of_last_full_bucket(blocks)
            )
        return blocks

    def migrate_blocks(
        self, protobuf_blocks: list[protobuf.BaseBlock]
    ) -> list["Block"]:
        ts = get_time_ms()
        self._blocks_persistence.write_blocks(protobuf_blocks)
        blocks = [
            Block.from_proto(protobuf_block) for protobuf_block in protobuf_blocks
        ]
        if blocks:
            self._chain_height_of_persisted_blocks = (
                self._get_height_of_last_full_bucket(blocks)
            )
        logger.info(
            f"Migrating blocks (write+deserialization) from DaoStateStore took {get_time_ms() - ts} ms"
        )
        return blocks

    def copy_from_resources(self, post_fix: str):
        ts = get_time_ms()
        dir_name = BsqBlocksStorageService.NAME
        resource_dir = dir_name + post_fix

        if self._blocks_dir.exists():
            logger.info(f"No resource directory was copied. {dir_name} exists already.")
            return

        try:
            file_names = p2p_list_resource_directory(resource_dir)
            if not file_names:
                logger.info(f"No files in directory. {resource_dir}")
                return

            self._blocks_dir.mkdir(parents=True, exist_ok=True)

            for file_name in file_names:
                destination_file = self._blocks_dir.joinpath(file_name)
                p2p_resource_to_file(
                    Path(resource_dir).joinpath(file_name), destination_file
                )

            logger.info(
                f"Copying {len(file_names)} resource files took {get_time_ms() - ts} ms"
            )
        except ResourceNotFoundException:
            logger.info(f"Directory {resource_dir} in resources does not exist.")
        except Exception as e:
            logger.error("", exc_info=e)

    def _get_height_of_last_full_bucket(self, blocks: list["Block"]) -> int:
        bucket_index = blocks[-1].height // BlocksPersistence.BUCKET_SIZE
        return bucket_index * BlocksPersistence.BUCKET_SIZE

    def remove_blocks_directory(self):
        self._blocks_persistence.remove_blocks_directory()

    def make_blocks_directory(self):
        if not self._blocks_dir.exists():
            self._blocks_dir.mkdir(parents=True, exist_ok=True)
