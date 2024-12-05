from typing import TYPE_CHECKING
from bisq.core.payment.payload.payment_method import PaymentMethod

if TYPE_CHECKING:
    from bisq.core.payment.payment_account import PaymentAccount

# TODO: implement rest of the class

class PaymentAccountUtil:

    @staticmethod
    def is_cryptocurrency_account(payment_account: "PaymentAccount"):
        return payment_account is not None and payment_account.payment_method in [
            PaymentMethod.BLOCK_CHAINS,
            PaymentMethod.BLOCK_CHAINS_INSTANT,
        ]
