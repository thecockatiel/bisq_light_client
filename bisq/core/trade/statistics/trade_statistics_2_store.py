from typing import cast
from bisq.core.network.p2p.persistence.persistable_network_payload_store import (
    PersistableNetworkPayloadStore,
)
from bisq.core.trade.statistics.trade_statistics_2 import TradeStatistics2
import pb_pb2 as protobuf


class TradeStatistics2Store(PersistableNetworkPayloadStore["TradeStatistics2"]):
    """
    We store only the payload in the PB file to save disc space. The hash of the payload can be created anyway and
    is only used as key in the map. So we have a hybrid data structure which is represented as list in the protobuffer
    definition and provide a hashMap for the domain access.
    """


    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            trade_statistics2_store=(self.get_builder())
        )

    def get_builder(self):
        items = cast(list["TradeStatistics2"], self.map.values())
        return protobuf.TradeStatistics2Store(
            items=[item.to_proto_trade_statistics_2() for item in items]
        )

    @staticmethod
    def from_proto(proto: protobuf.TradeStatistics2Store) -> "TradeStatistics2Store":
        return TradeStatistics2Store(
            (TradeStatistics2.from_proto(item) for item in proto.items)
        )
