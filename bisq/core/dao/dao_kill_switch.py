from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.version import Version
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.exceptions.dao_disabled_exception import DaoDisabledException

if TYPE_CHECKING:
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.filter.filter import Filter


class DaoKillSwitch(DaoSetupService):
    def __init__(self, filter_manager: "FilterManager"):
        self._filter_manager = filter_manager
        self.dao_disabled = False
        self._subscriptions: list[Callable[[], None]] = []

    def add_listeners(self):
        self._subscriptions.append(
            self._filter_manager.filter_property.add_listener(
                lambda e: self._apply_filter(e.new_value)
            )
        )

    def start(self):
        self._apply_filter(self._filter_manager.get_filter())

    def _apply_filter(self, filter: "Filter"):
        if filter is None:
            self.dao_disabled = False
            return

        require_update_to_new_version = False
        disable_dao_below_version = filter.disable_dao_below_version
        if disable_dao_below_version:
            require_update_to_new_version = Version.is_new_version(
                disable_dao_below_version
            )

        self.dao_disabled = require_update_to_new_version or filter.disable_dao

    def assert_dao_is_not_disabled(self):
        if self.dao_disabled:
            raise DaoDisabledException(
                "The DAO features have been disabled by the Bisq developers. "
                "Please check out the Bisq Forum for further information."
            )

    def shut_down(self):
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()
