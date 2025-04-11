from bisq.common.protocol.proto_util import ProtoUtil
from pb_pb2 import GetInventoryResponse


def is_patched_pb_working_as_expected():
    s = GetInventoryResponse(
        inventory=ProtoUtil.to_string_map_entry_list(
            {
                "capabilities": "1",
                "accountAgeWitnessHash": "2",
            }
        )
    )

    # try to round trip the stable example to make sure it stays the same
    for i in range(5):
        round_tripped = GetInventoryResponse(
            inventory=ProtoUtil.to_string_map_entry_list(
                ProtoUtil.to_string_map(s.inventory)
            )
        )
        if s.SerializeToString() != round_tripped.SerializeToString():
            return False
        s = round_tripped

    return True
