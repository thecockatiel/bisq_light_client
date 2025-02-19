from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.node.full.raw_block import RawBlock


class RequiredReorgFromSnapshotException(Exception):

    def __init__(self, raw_block: "RawBlock"):
        self.raw_block = raw_block
