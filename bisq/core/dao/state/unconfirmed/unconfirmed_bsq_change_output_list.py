from collections.abc import Collection
from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.persistable.persistable_list import PersistableList
import pb_pb2 as protobuf
from bisq.core.dao.state.unconfirmed.unconfirmed_tx_output import UnconfirmedTxOutput


class UnconfirmedBsqChangeOutputList(PersistableList["UnconfirmedTxOutput"]):

    def __init__(self, collection: Optional[Collection["UnconfirmedTxOutput"]] = None):
        super().__init__(collection)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            unconfirmed_bsq_change_output_list=protobuf.UnconfirmedBsqChangeOutputList(
                unconfirmed_tx_output=[
                    output.to_proto_message() for output in self.list
                ]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.UnconfirmedBsqChangeOutputList):
        return UnconfirmedBsqChangeOutputList(
            [
                UnconfirmedTxOutput.from_proto(output)
                for output in proto.unconfirmed_tx_output
            ]
        )

    def contains_tx_output(self, tx_output: "UnconfirmedTxOutput") -> bool:
        return any(output.key == tx_output.key for output in self.list)
