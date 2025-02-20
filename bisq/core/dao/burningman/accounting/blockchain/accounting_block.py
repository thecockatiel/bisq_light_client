from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx import AccountingTx
import pb_pb2 as protobuf


# Block data is aggressively optimized for minimal size.
# Block has 21 bytes base cost
# Tx has 2 byte base cost.
# TxOutput has variable byte size depending on name length, usually about 10-20 bytes.
# Some extra overhead of a few bytes is present depending on lists filled or not.
# Example fee tx (1 output) has about 40 bytes
# Example DPT tx with 2 outputs has about 60 bytes, typical DPT with 15-20 outputs might have 500 bytes.
# 2 year legacy BM had about 100k fee txs and 1000 DPTs. Would be about 4MB for fee txs and 500kB for DPT.
# As most blocks have at least 1 tx we might not have empty blocks.
# With above estimates we can expect about 2 MB growth per year.


class AccountingBlock(NetworkPayload):

    def __init__(
        self,
        height: int,
        time_in_sec: int,
        truncated_hash: bytes,
        truncated_previous_block_hash: bytes,
        txs: tuple[AccountingTx],
    ):
        self.height = height
        self.time_in_sec = time_in_sec
        # We use only last 4 bytes of 32 byte hash to save space.
        # We use a byte array for flexibility if we would need to change the length of the hash later
        self.truncated_hash = truncated_hash
        self.truncated_previous_block_hash = truncated_previous_block_hash
        self.txs = txs

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.AccountingBlock:
        return protobuf.AccountingBlock(
            height=self.height,
            time_in_sec=self.time_in_sec,
            truncated_hash=self.truncated_hash,
            truncated_previous_block_hash=self.truncated_previous_block_hash,
            txs=[tx.to_proto_message() for tx in self.txs],
        )

    @staticmethod
    def from_proto(proto: protobuf.AccountingBlock) -> "AccountingBlock":
        txs = tuple(AccountingTx.from_proto(tx) for tx in proto.txs)
        return AccountingBlock(
            height=proto.height,
            time_in_sec=proto.time_in_sec,
            truncated_hash=proto.truncated_hash,
            truncated_previous_block_hash=proto.truncated_previous_block_hash,
            txs=txs,
        )

    @property
    def date(self) -> int:
        return self.time_in_sec * 1000

    def __str__(self) -> str:
        return (
            f"AccountingBlock{{\n"
            f"    height={self.height},\n"
            f"    time_in_sec={self.time_in_sec},\n"
            f"    truncated_hash={self.truncated_hash.hex()},\n"
            f"    truncated_previous_block_hash={self.truncated_previous_block_hash.hex()},\n"
            f"    txs={self.txs}\n"
            f"}}"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, AccountingBlock):
            return False
        return (
            self.height == other.height
            and self.time_in_sec == other.time_in_sec
            and self.truncated_hash == other.truncated_hash
            and self.truncated_previous_block_hash
            == other.truncated_previous_block_hash
            and self.txs == other.txs
        )

    def __hash__(self):
        return hash(
            (
                self.height,
                self.time_in_sec,
                self.truncated_hash,
                self.truncated_previous_block_hash,
                self.txs,
            )
        )
