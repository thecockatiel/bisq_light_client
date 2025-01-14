from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.reject_code import RejectCode
    from bitcoinj.core.sha_256_hash import Sha256Hash

# TODO
class RejectMessage:

    def __init__(
        self,
        params: "NetworkParameters",
        code: "RejectCode",
        hash: "Sha256Hash",
        message: str,
        reason: str,
    ) -> None:
        self.params = params
        self.code = code
        self.message_hash = hash
        self.message = message
        self.reason = reason

    def get_rejected_object_hash(self):
        """Provides the hash of the rejected object (if getRejectedMessage() is either "tx" or "block"), otherwise null."""
        return self.message_hash

    def get_reason_code(self):
        """The reason code given for why the peer rejected the message."""
        return self.code
