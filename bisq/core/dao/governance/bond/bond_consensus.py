from typing import Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import byte_array_to_integer, integer_to_byte_array
from bisq.common.version import Version
from bisq.core.dao.governance.bond.lockup.lockup_reason import LockupReason
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from io import BytesIO

logger = get_logger(__name__)


class BondConsensus:
    # In the UI we don't allow 0 as that would mean that the tx gets spent
    # in the same block as the unspent tx and we don't support unconfirmed txs in the DAO. Technically though 0
    # works as well.
    MIN_LOCK_TIME = 1

    # Max value is max of a short int as we use only 2 bytes in the opReturn for the lockTime
    MAX_LOCK_TIME = 65535

    @staticmethod
    def get_lockup_op_return_data(
        lock_time: int, lockup_reason: "LockupReason", hash_value: bytes
    ) -> bytes:
        # PushData of <= 4 bytes is converted to int when returned from bitcoind and not handled the way we
        # require by btcd-cli4j, avoid opReturns with 4 bytes or less
        with BytesIO() as outputStream:
            outputStream.write(bytes([OpReturnType.LOCKUP.type]))
            outputStream.write(Version.LOCKUP)
            outputStream.write(bytes([lockup_reason.id]))
            bytes_ = integer_to_byte_array(lock_time, 2)
            outputStream.write(bytes_)
            outputStream.write(hash_value)
            return outputStream.getvalue()

    @staticmethod
    def has_op_return_data_valid_length(op_return_data: bytes) -> bool:
        return len(op_return_data) == 25

    @staticmethod
    def get_lock_time(op_return_data: bytes) -> int:
        return byte_array_to_integer(op_return_data[3:5])

    @staticmethod
    def get_hash_from_op_return_data(op_return_data: bytes) -> bytes:
        return op_return_data[5:25]

    @staticmethod
    def is_lock_time_in_valid_range(lock_time: int) -> bool:
        return BondConsensus.MIN_LOCK_TIME <= lock_time <= BondConsensus.MAX_LOCK_TIME

    @staticmethod
    def get_lockup_reason(op_return_data: bytes) -> "Optional[LockupReason]":
        return LockupReason.get_lockup_reason(op_return_data[2])

    @staticmethod
    def is_lock_time_over(unlock_block_height: int, current_block_height: int) -> bool:
        return current_block_height >= unlock_block_height
