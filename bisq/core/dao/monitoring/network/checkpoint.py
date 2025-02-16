from dataclasses import dataclass, field

from bisq.common.util.utilities import bytes_as_hex_string


@dataclass
class Checkpoint:
    height: int
    hash: bytes
    passed: bool = field(default=False)

    def __str__(self):
        return (
            f"Checkpoint {{\n"
            f"     height={self.height},\n"
            f"     hash={bytes_as_hex_string(self.hash)},\n"
            f"     passed={self.passed}\n"
            f"}}"
        )
