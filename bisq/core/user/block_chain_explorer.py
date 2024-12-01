from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
import proto.pb_pb2 as protobuf

class BlockChainExplorer(PersistablePayload):
    def __init__(self, name: str, tx_url: str, address_url: str):
        self.name = name
        self.tx_url = tx_url
        self.address_url = address_url

    def to_proto_message(self):
        return protobuf.BlockChainExplorer(
            name=self.name,
            tx_url=self.tx_url,
            address_url=self.address_url
        )

    @staticmethod
    def from_proto(proto: protobuf.BlockChainExplorer) -> 'BlockChainExplorer':
        return BlockChainExplorer(
            name=proto.name,
            tx_url=proto.tx_url,
            address_url=proto.address_url,
        )
