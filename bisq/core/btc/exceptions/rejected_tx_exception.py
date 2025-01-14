from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bitcoinj.core.reject_message import RejectMessage


class RejectedTxException(RuntimeError):
    """
    Used in case the broadcasting of a tx did not succeed in the expected time.
    The broadcast can still succeed at a later moment though.
    """

    def __init__(
        self,
        message: str,
        reject_message: "RejectMessage",
    ):
        super().__init__(message)
        self.reject_message = reject_message
        obj_hash = reject_message.get_rejected_object_hash()
        self.tx_id = str(obj_hash) if obj_hash is not None else None

    def __str__(self) -> str:
        return (
            f"RejectedTxException{{\n"
            f"    rejectMessage={self.reject_message},\n"
            f"    txId='{self.tx_id}'\n"
            f"}} {super().__str__()}"
        )
