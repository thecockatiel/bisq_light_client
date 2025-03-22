from enum import Enum
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from typing import List, Set, Optional, Type, TypeVar, Iterable, Collection
from collections.abc import Callable
from google.protobuf import message
from google.protobuf.any_pb2 import Any

from bisq.common.proto import Proto
from bisq.common.setup.log_setup import get_logger
from utils.ordered_containers import OrderedSet

T = TypeVar('T', bound=message.Message)

logger = get_logger(__name__)

class ProtoUtil:

    @staticmethod
    def byte_set_from_proto_byte_string_list(byte_string_list: List[Any]) -> Set[bytes]:
        return {b.SerializeToString() for b in byte_string_list}

    @staticmethod
    def string_or_none_from_proto(proto: str) -> Optional[str]:
        return None if not proto else proto

    @staticmethod
    def byte_array_or_none_from_proto(proto: bytes) -> Optional[bytes]:
        return None if not proto else proto

    @staticmethod
    def enum_from_proto(enum_type: Type[T], proto_enum_type: "EnumTypeWrapper", proto_enum_value: Optional[Any] = None) -> Optional[T]:
        try:
            if proto_enum_value is None:
                enum_name = proto_enum_type
            else:
                enum_name = proto_enum_type.Name(proto_enum_value)
            return enum_type[enum_name]
        except:
            try:
                result = enum_type["UNDEFINED"]
                logger.debug(f"We try to lookup for an enum entry with name 'UNDEFINED' and use that if available, otherwise the enum is null. enum={result}")
                return result
            except:
                return None

    @staticmethod
    def proto_enum_from_enum(proto_enum_type: Type[T], enum: Optional[Enum]) -> Optional[T]:
        enum_name = enum.name if enum is not None else "UNDEFINED"
        try:
            return proto_enum_type.Value(enum_name)
        except:
            try:
                result = proto_enum_type.Value["UNDEFINED"]
                logger.debug(f"We try to lookup for an enum entry with name 'UNDEFINED' and use that if available, otherwise the enum is null. enum={result}")
                return result
            except:
                return None

    @staticmethod
    def proto_enum_to_str(proto_enum_type: Type[T], proto_enum_value: Optional[Any] = None) -> Optional[T]:
        try:
            if proto_enum_value is None:
                enum_name = "None"
            else:
                enum_name = proto_enum_type.Name(proto_enum_value)
            return enum_name
        except:
            return "UNDEFINED"

    # NOTE: check for improvements
    @staticmethod
    def collection_to_proto(collection: Collection['Proto'], message_type: Type[T]) -> Iterable[T]:
        result = []
        for e in collection:
            message = e.to_proto_message()
            try:
                result.append(message_type.FromString(message.SerializeToString()))
            except Exception as e:
                logger.error(f"Message could not be cast. message={message}, message_type={message_type}")
        return result

    @staticmethod
    def collection_to_proto_with_extra(collection: Collection['Proto'], extra: Callable[[message.Message], T]) -> Iterable[T]:
        return [extra(o.to_proto_message()) for o in collection]

    @staticmethod
    def protocol_string_list_to_list(protocol_string_list: List[str]) -> List[str]:
        return [] if not protocol_string_list else list(protocol_string_list)

    @staticmethod
    def protocol_string_list_to_set(protocol_string_list: List[str]) -> "OrderedSet[str]":
        return OrderedSet() if not protocol_string_list else OrderedSet(protocol_string_list)