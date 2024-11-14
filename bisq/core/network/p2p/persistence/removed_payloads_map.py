from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
import proto.pb_pb2 as protobuf


class RemovedPayloadsMap:
    def __init__(self, date_by_hashes: dict["StorageByteArray", int] = None):
        if date_by_hashes is None:
            date_by_hashes = {}
        self.date_by_hashes: dict["StorageByteArray", int] = date_by_hashes

    # Protobuf map only supports strings or integers as key, but no bytes or complex object so we convert the
    # bytes to a hex string, otherwise we would need to make a extra value object to wrap it.
    def to_proto_message(self):
        # Convert ByteArray keys to hex strings for protobuf compatibility
        proto_map = {key.get_hex(): value for key, value in self.date_by_hashes.items()}

        message = protobuf.RemovedPayloadsMap(date_by_hashes=proto_map)
        envelope = protobuf.PersistableEnvelope(removed_payloads_map=message)
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.RemovedPayloadsMap):
        # Convert hex strings back to ByteArray keys
        date_by_hashes = {
            StorageByteArray(bytes.fromhex(key)): value
            for key, value in proto.date_by_hashes.items()
        }
        return RemovedPayloadsMap(date_by_hashes)

    def __str__(self):
        return f"RemovedPayloadsMap{{\n     dateByHashes={self.date_by_hashes}\n}}"
