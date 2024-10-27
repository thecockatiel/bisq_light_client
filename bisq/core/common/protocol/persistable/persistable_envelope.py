from bisq.core.common.envelope import Envelope
from google.protobuf.message import Message

class PersistableEnvelope(Envelope):
    def to_persistable_message(self) -> Message:
        return self.to_proto_message()

    def get_default_storage_file_name(self) -> str:
        return self.__class__.__name__