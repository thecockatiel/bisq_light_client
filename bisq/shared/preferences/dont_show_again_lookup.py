
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.shared.preferences.preferences import Preferences

class DontShowAgainLookup:
    preferences = None

    @staticmethod
    def set_preferences(preferences: "Preferences"):
        DontShowAgainLookup.preferences = preferences

    @staticmethod
    def show_again(key: str) -> bool:
        return DontShowAgainLookup.preferences.show_again(key)

    @staticmethod
    def dont_show_again(key: str, dont_show_again: bool):
        DontShowAgainLookup.preferences.dont_show_again(key, dont_show_again)
