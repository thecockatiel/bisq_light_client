from typing import TYPE_CHECKING, Optional
from bisq.asset.asset import Asset
from bisq.core.dao.governance.asset.asset_state import AssetState
from bisq.core.locale.currency_util import get_currency_name_and_code

if TYPE_CHECKING:
    from bisq.core.dao.governance.asset.fee_payment import FeePayment


class StatefulAsset:

    def __init__(self, asset: "Asset"):
        self._asset = asset
        self.asset_state = AssetState.UNDEFINED
        self._fee_payments: list["FeePayment"] = []
        self.trade_volume: int = 0
        self.look_back_period_in_days: int = 0

    @property
    def name_and_code(self) -> str:
        return get_currency_name_and_code(self.ticker_symbol)

    @property
    def ticker_symbol(self) -> str:
        return self._asset.get_ticker_symbol()

    @property
    def last_fee_payment(self) -> Optional["FeePayment"]:
        return self._fee_payments[-1] if self._fee_payments else None

    def get_total_fees_paid(self) -> int:
        return sum(fee_payment.fee for fee_payment in self._fee_payments)

    def get_fee_of_trial_period(self) -> int:
        last_fee_payment = self.last_fee_payment
        if last_fee_payment and self.asset_state == AssetState.IN_TRIAL_PERIOD:
            return last_fee_payment.fee
        return 0

    @property
    def is_active(self) -> bool:
        return not self.was_removed_by_voting and not self.is_de_listed

    @property
    def was_removed_by_voting(self) -> bool:
        return self.asset_state == AssetState.REMOVED_BY_VOTING

    @property
    def is_de_listed(self) -> bool:
        return self.asset_state == AssetState.DE_LISTED

    def __str__(self) -> str:
        return (
            f"StatefulAsset{{\n"
            f"    asset={self._asset},\n"
            f"    assetState={self.asset_state},\n"
            f"    feePayments={self._fee_payments},\n"
            f"    tradeVolume={self.trade_volume},\n"
            f"    lookBackPeriodInDays={self.look_back_period_in_days}\n"
            f"}}"
        )
