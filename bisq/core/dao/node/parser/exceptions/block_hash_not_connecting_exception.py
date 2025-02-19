from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.dao.node.full.raw_block import RawBlock


class BlockHashNotConnectingException(Exception):

    def __init__(self, raw_block: "RawBlock"):
        self.raw_block = raw_block

    def __str__(self):
        return (
            f"BlockHashNotConnectingException{{\n"
            f"     raw_block.hash={self.raw_block.hash}\n"
            f"     raw_block.height={self.raw_block.height}\n"
            f"     raw_block.previous_block_hash={self.raw_block.previous_block_hash}\n"
            f"}} {super().__str__()}"
        )
