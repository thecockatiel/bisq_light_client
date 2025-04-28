from enum import IntEnum
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.utilities import get_random_id
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
import pb_pb2 as protobuf


class PreliminaryRequestPreference(IntEnum):
    FOR_ALL_USERS = 0
    ONLY_ONCE = 1

    def to_proto_message(self):
        return self.value

    @staticmethod
    def from_proto(proto: int):
        for preference in PreliminaryRequestPreference:
            if proto == preference.value:
                return preference
        raise IllegalArgumentException(
            f"Invalid proto value for PreliminaryRequestPreference: {proto}"
        )


class UserManagerPayload(PersistableEnvelope):
    def __init__(
        self,
        active_user_id: str = None,
        user_alias_entries: dict[str, str] = None,
        keep_alive_on_switch: bool = None,
        init_all_at_once: bool = None,
        preliminary_request_preference=None,
    ):
        if not active_user_id:
            active_user_id = str(get_random_id(8))
        if not user_alias_entries:
            user_alias_entries = {active_user_id: ""}
        if keep_alive_on_switch is None:
            keep_alive_on_switch = False
        if init_all_at_once is None:
            init_all_at_once = False
        if preliminary_request_preference is None:
            preliminary_request_preference = PreliminaryRequestPreference.FOR_ALL_USERS
        self.keep_alive_on_switch = keep_alive_on_switch
        self.init_all_at_once = init_all_at_once
        self.preliminary_request_preference = preliminary_request_preference
        self.active_user_id = active_user_id
        # user alias entries acts as both the user list and a tool for aliasing users
        self.user_alias_entries = user_alias_entries
        """user_id -> alias"""

    def to_proto_message(self) -> protobuf.PersistableEnvelope:
        payload = protobuf.UserManagerPayload(
            active_user_id=self.active_user_id,
            user_alias_entries=ProtoUtil.to_string_map_entry_list(
                self.user_alias_entries
            ),
            keep_alive_on_switch=self.keep_alive_on_switch,
            init_all_at_once=self.init_all_at_once,
            preliminary_request_preference=self.preliminary_request_preference.to_proto_message(),
        )
        envelope = protobuf.PersistableEnvelope()
        envelope.user_manager_payload.CopyFrom(payload)
        return envelope

    @staticmethod
    def from_proto(
        proto: protobuf.UserManagerPayload,
    ) -> "UserManagerPayload":
        return UserManagerPayload(
            active_user_id=proto.active_user_id,
            user_alias_entries=ProtoUtil.to_string_map(proto.user_alias_entries),
            keep_alive_on_switch=proto.keep_alive_on_switch,
            init_all_at_once=proto.init_all_at_once,
            preliminary_request_preference=PreliminaryRequestPreference.from_proto(
                proto.preliminary_request_preference
            ),
        )
