from typing import Any, Optional, Union
from bitcoinj.base.coin import Coin


class ProposalValidationException(Exception):
    def __init__(self, message: Union[str, Exception], *, tx: Optional[Any] = None, requested_bsq: Optional[Coin] = None, min_request_amount: Optional[Coin] = None):
        super().__init__(message)
        self.message = str(message)
        self.requested_bsq = requested_bsq
        self.min_request_amount = min_request_amount
        self.tx = tx

    def __str__(self):
        return "ProposalValidationException{" + \
                "\n     requestedBsq=" + str(self.requested_bsq) + \
                ",\n     minRequestAmount=" + str(self.min_request_amount) + \
                ",\n     tx=" + str(self.tx) + \
                "\n} " + super().__str__()

