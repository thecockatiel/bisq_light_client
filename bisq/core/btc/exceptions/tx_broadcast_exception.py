from typing import Optional


class TxBroadcastException(Exception):
    """
    Used in case the broadcasting of a tx did not succeed in the expected time.
    The broadcast can still succeed at a later moment though.
    """

    def __init__(
        self, message: str, cause: Optional[Exception] = None, tx_id: Optional[str] = None
    ):
        super().__init__(message)
        if cause:
            self.__cause__ = cause

        self.tx_id = tx_id

    def __str__(self):
        return str(self.args[0])

    def __repr__(self):
        return (
            f"TxBroadcastException{{\n    tx_id='{self.tx_id}'\n}} {super().__str__()}"
        )
