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
    map = {
        "capabilities": "1",
        "accountAgeWitnessHash": "2",
    }  # order matters for our test
    u = UnstableExample(extra_data=map)
    s = StableExample(extra_data=map_to_stable_extra_data(map))

    first_test = u.SerializeToString() == s.SerializeToString()

    round_tripped_stable = StableExample(
        extra_data=map_to_stable_extra_data(stable_extra_data_to_map(s.extra_data))
    )

    second_test = s.SerializeToString() == round_tripped_stable.SerializeToString()

    return first_test and second_test

