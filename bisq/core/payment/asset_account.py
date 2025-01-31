from abc import ABC
from bisq.core.payment.payload.assets_account_payload import AssetsAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class AssetAccount(PaymentAccount, ABC):

    def __init__(self, payment_method: "PaymentMethod"):
        super().__init__(payment_method)

    @property
    def address(self) -> str:
        self._assets_account_payload.address

    @address.setter
    def address(self, address: str) -> None:
        self._assets_account_payload.address = address

    @property
    def _assets_account_payload(self) -> "AssetsAccountPayload":
        return self.payment_account_payload
