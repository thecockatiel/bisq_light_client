from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope

import pb_pb2 as protobuf


class BsqBlockStore(PersistableEnvelope):
    """Wrapper for list of blocks"""

    def __init__(self, blocks_as_proto: list[protobuf.BaseBlock]):
        self.blocks_as_proto = blocks_as_proto

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            bsq_block_store=protobuf.BsqBlockStore(blocks=self.blocks_as_proto)
        )

    @staticmethod
    def from_proto(proto: protobuf.BsqBlockStore):
        return BsqBlockStore(proto.blocks)
