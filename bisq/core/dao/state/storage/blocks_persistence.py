import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from bisq.common.file.file_util import (
    create_new_file,
    create_temp_file,
    delete_directory,
    rename_file,
)
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.state.storage.bsq_block_store import BsqBlockStore
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import pb_pb2 as protobuf
from proto.delimited_protobuf import read_delimited, write_delimited
from utils.time import get_time_ms
import tempfile

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistence_proto_resolver import (
        PersistenceProtoResolver,
    )

logger = get_logger(__name__)


class BlocksPersistence:
    BUCKET_SIZE = 1000  # results in about 1 MB files and about 1 new file per week

    def __init__(
        self,
        storage_dir: Path,
        file_name: str,
        persistence_proto_resolver: "PersistenceProtoResolver",
    ):
        self._storage_dir = storage_dir
        self._file_name = file_name
        self._persistence_proto_resolver = persistence_proto_resolver
        self._used_temp_file_path: Optional[Path] = None

    def write_blocks(self, protobuf_blocks: list[protobuf.BaseBlock]):
        start_time = get_time_ms()
        if not self._storage_dir.exists():
            self._storage_dir.mkdir(parents=True, exist_ok=True)

        temp = []
        bucket_index = 0
        for block in protobuf_blocks:
            temp.append(block)
            height = block.height
            bucket_index = height // BlocksPersistence.BUCKET_SIZE
            remainder = height % BlocksPersistence.BUCKET_SIZE
            is_last_bucket_item = remainder == 0
            if is_last_bucket_item:
                first = (
                    bucket_index * BlocksPersistence.BUCKET_SIZE
                    - BlocksPersistence.BUCKET_SIZE
                    + 1
                )
                last = bucket_index * BlocksPersistence.BUCKET_SIZE
                storage_file = self._storage_dir.joinpath(
                    f"{self._file_name}_{first}-{last}"
                )
                self._write_to_disk(storage_file, BsqBlockStore(temp))
                temp = []

        if temp:
            bucket_index += 1
            first = (
                bucket_index * BlocksPersistence.BUCKET_SIZE
                - BlocksPersistence.BUCKET_SIZE
                + 1
            )
            last = bucket_index * BlocksPersistence.BUCKET_SIZE
            storage_file = self._storage_dir.joinpath(
                f"{self._file_name}_{first}-{last}"
            )
            self._write_to_disk(storage_file, BsqBlockStore(temp))

        logger.info(
            f"Write {len(protobuf_blocks)} blocks to disk took {get_time_ms() - start_time} msec"
        )

    def remove_blocks_directory(self):
        if self._storage_dir.exists():
            try:
                delete_directory(self._storage_dir)
            except Exception as e:
                logger.error(
                    f"Failed to delete directory {self._storage_dir}", exc_info=e
                )

    def read_blocks(self, from_height: int, to_height: int) -> list[protobuf.BaseBlock]:
        if not self._storage_dir.exists():
            self._storage_dir.mkdir(parents=True, exist_ok=True)

        start_time = get_time_ms()
        blocks = []
        start_bucket = from_height // BlocksPersistence.BUCKET_SIZE + 1
        end_bucket = to_height // BlocksPersistence.BUCKET_SIZE + 1

        for bucket_index in range(start_bucket, end_bucket + 1):
            bucket_blocks = self._read_bucket(bucket_index)
            blocks.extend(bucket_blocks)

        logger.info(
            f"Reading {len(blocks)} blocks took {get_time_ms() - start_time} msec"
        )
        return blocks

    def _read_bucket(self, bucket_index: int) -> list[protobuf.BaseBlock]:
        first = (
            bucket_index * BlocksPersistence.BUCKET_SIZE
            - BlocksPersistence.BUCKET_SIZE
            + 1
        )
        last = bucket_index * BlocksPersistence.BUCKET_SIZE
        storage_file = self._storage_dir.joinpath(f"{self._file_name}_{first}-{last}")
        if not storage_file.exists():
            return []

        try:
            with storage_file.open("rb") as f:
                proto = read_delimited(f, protobuf.PersistableEnvelope)
                if proto is None:
                    return []
                bsq_block_store = self._persistence_proto_resolver.from_proto(proto)
                if not isinstance(bsq_block_store, BsqBlockStore):
                    raise IllegalStateException(
                        f"Expected BsqBlockStore but got {bsq_block_store.__class__.__name__}"
                    )
                return bsq_block_store.blocks_as_proto
        except Exception as e:
            logger.info(f"Reading {storage_file} failed with {e}")
            return []

    def _write_to_disk(self, storage_file: Path, bsq_block_store: BsqBlockStore):
        temp_file = None
        try:
            temp_file = (
                create_new_file(self._used_temp_file_path)
                if self._used_temp_file_path
                else create_temp_file(
                    f"temp_{self._file_name}", None, self._storage_dir
                )
            )

            with temp_file.open("wb") as f:
                write_delimited(f, bsq_block_store.to_proto_message())
                # Attempt to force the bits to hit the disk. In reality the OS or hard disk itself may still decide
                # to not write through to physical media for at least a few seconds, but this is the best we can do.
                f.flush()
                os.fsync(f.fileno())

            rename_file(temp_file, storage_file)
            self._used_temp_file_path = temp_file
        except Exception as e:
            # If an error occurred, don't attempt to reuse this path again, in case temp file cleanup fails.
            self._used_temp_file_path = None
            logger.error(
                f"Error at saveToFile, storageFile={self._file_name}", exc_info=e
            )
        finally:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink(missing_ok=True)
                except Exception as e:
                    logger.error("Cannot delete temp file.", exc_info=e)
