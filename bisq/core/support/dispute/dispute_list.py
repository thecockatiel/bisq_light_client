from abc import ABC
from typing import TypeVar
from bisq.common.protocol.persistable.persistable_list_as_observable import (
    PersistableListAsObservable,
)
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload


_T = TypeVar("T", bound=PersistablePayload)


class DisputeList(PersistableListAsObservable[_T], ABC):
    """
    Holds a List of Dispute objects.

    Calls to the List are delegated because this class intercepts the add/remove calls so changes
    can be saved to disc.
    """

    pass
