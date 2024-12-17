from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bitcoinj.core.address import Address
    from bitcoinj.core.network_parameters import NetworkParameters


# TODO
class Script:

    def __init__(self, program_bytes: Optional[bytes] = None):
        self.program = program_bytes or bytes()

    def hex(self) -> str:
        return self.program.hex()

    def get_to_address(self, params: "NetworkParameters") -> "Address":
        raise RuntimeError("Script.get_to_address Not implemented yet")
