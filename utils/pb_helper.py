from typing import Iterable
from spb_pb2 import StableExtraData, StableExample, UnstableExample


def map_to_stable_extra_data(map: dict[str, str]):
    if not map:
        return None
    return [StableExtraData(key=k, value=v) for k, v in map.items()]


def stable_extra_data_to_map(extra_data: Iterable[StableExtraData]):
    if not extra_data:
        return None
    return {v.key: v.value for v in extra_data}


def is_patched_pb_working_as_expected():
    s = StableExample(
        extra_data=map_to_stable_extra_data(
            {
                "capabilities": "1",
                "accountAgeWitnessHash": "2",
            }
        )
    )

    # try to round trip the stable example to make sure it stays the same
    for i in range(5):
        round_tripped = StableExample(
            extra_data=map_to_stable_extra_data(stable_extra_data_to_map(s.extra_data))
        )
        if s.SerializeToString() != round_tripped.SerializeToString():
            return False
        s = round_tripped

    return True
