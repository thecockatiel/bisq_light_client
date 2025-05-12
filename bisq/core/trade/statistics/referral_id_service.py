from typing import TYPE_CHECKING, Optional
from bisq.core.trade.statistics.referral_id import ReferralId

if TYPE_CHECKING:
    from bisq.shared.preferences.preferences import Preferences

class ReferralIdService:
    def __init__(self, preferences: "Preferences") -> None:
        self.preferences = preferences
        self._referral_id: Optional[str] = None

    def verify(self, referral_id: str) -> bool:
        return any(e.name == referral_id for e in ReferralId)

    def get_optional_referral_id(self) -> Optional[str]:
        referral_id = self.preferences.get_referral_id()
        if referral_id and self.verify(referral_id):
            self._referral_id = referral_id
        else:
            self._referral_id = None
        
        return self._referral_id

    def set_referral_id(self, referral_id: Optional[str]) -> None:
        if not referral_id or self.verify(referral_id):
            self._referral_id = referral_id
            self.preferences.set_referral_id(referral_id)
