from datetime import timedelta, datetime
from bisq.common.protocol.network.get_data_response_priority import (
    GetDataResponsePriority,
)
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.network.p2p.storage.payload.data_tolerant_payload import (
    DateTolerantPayload,
)
from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
    PersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.payload.process_once_persistable_network_payload import (
    ProcessOncePersistableNetworkPayload,
)
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
import proto.pb_pb2 as protobuf

logger = get_logger(__name__)


class AccountAgeWitness(
    ProcessOncePersistableNetworkPayload,  DateTolerantPayload, PersistableNetworkPayload
):
    TOLERANCE_MS = int(timedelta(days=1).total_seconds() * 1000)

    def __init__(self, hash_: bytes, date: int):
        super().__init__()
        self._hash = hash_  # Ripemd160(Sha256(concatenated accountHash, signature and sigPubKey)); 20 bytes
        self._date = date  # 8 byte

    def to_proto_message(self) -> protobuf.PersistableNetworkPayload:
        witness = protobuf.AccountAgeWitness(
            hash=bytes(self._hash),
            date=self._date,
        )
        return protobuf.PersistableNetworkPayload(
            account_age_witness=witness
        )
        
    def to_proto_account_age_witness(self) -> protobuf.AccountAgeWitness:
        return self.to_proto_message().account_age_witness

    @staticmethod
    def from_proto(proto: protobuf.AccountAgeWitness) -> "AccountAgeWitness":
        hash_ = proto.hash
        if len(hash_) != 20:
            logger.warning("We got a hash which is not 20 bytes")
            hash_ = bytes()
        return AccountAgeWitness(hash_, proto.date)

    def get_get_data_response_priority(self) -> "GetDataResponsePriority":
        return GetDataResponsePriority.MID

    def is_date_in_tolerance(self, clock) -> bool:
        # We don't allow older or newer than 1 day.
        # Preventing forward dating is also important to protect against a sophisticated attack
        return abs(clock.millis() - self._date) <= self.TOLERANCE_MS

    def verify_hash_size(self) -> bool:
        return len(self._hash) == 20

    def get_hash(self) -> bytes:
        return self._hash
    
    @property
    def date(self):
        return self._date
    
    def get_hash_as_byte_array(self):
        return StorageByteArray(self._hash)
    
    def __str__(self):
        return (f"AccountAgeWitness{{\n"
                f"     hash={bytes_as_hex_string(self._hash)},\n"
                f"     date={datetime.fromtimestamp(self._date / 1000)}\n"
                f"}}")


