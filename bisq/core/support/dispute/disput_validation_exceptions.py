from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.support.dispute.dispute import Dispute


class DisputeValidationException(Exception):
    def __init__(self, dispute: "Dispute", msg: str):
        super().__init__(msg)
        self._dispute = dispute

    @property
    def dispute(self):
        return self._dispute


class DisputeValidationNodeAddressException(DisputeValidationException):
    def __init__(self, dispute, msg):
        super().__init__(dispute, msg)


class DisputeValidationAddressException(DisputeValidationException):
    def __init__(self, dispute, msg):
        super().__init__(dispute, msg)


class DisputeValidationReplayException(DisputeValidationException):
    def __init__(self, dispute, msg):
        super().__init__(dispute, msg)
