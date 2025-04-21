from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.key_ring import KeyRing
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.locale.crypto_currency import CryptoCurrency
from bisq.core.locale.language_util import LanguageUtil
from bisq.core.locale.res import Res
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.bsq_swap_account import BsqSwapAccount

from bisq.core.user.user_payload import UserPayload
from utils.data import (
    ObservableChangeEvent,
    ObservableSet,
    SimpleProperty,
    SimplePropertyChangeEvent,
)

if TYPE_CHECKING:
    from bisq.core.user.cookie import Cookie
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.notifications.alerts.market.market_alert_filter import (
        MarketAlertFilter,
    )
    from bisq.core.notifications.alerts.price.price_alert_filter import PriceAlertFilter
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator import Arbitrator
    from bisq.core.support.dispute.mediation.mediator.mediator import Mediator
    from bisq.core.support.refund.refundagent.refund_agent import RefundAgent
    from bisq.core.alert.alert import Alert
    from bisq.core.filter.filter import Filter
    from bisq.common.persistence.persistence_manager import PersistenceManager


class User(PersistedDataHost):
    """
    The User is persisted locally.
    It must never be transmitted over the wire (messageKeyPair contains private key!).
    """

    def __init__(
        self,
        persistence_manager: "PersistenceManager[UserPayload]",
        key_ring: "KeyRing",
    ):
        super().__init__()
        self.persistence_manager = persistence_manager
        self.key_ring = key_ring

        self.payment_accounts_observable = ObservableSet["PaymentAccount"]()
        self.current_payment_account_property = SimpleProperty["PaymentAccount"]()

        self.user_payload = UserPayload()
        self.is_payment_account_import: bool = False

    def read_persisted(self, complete_handler: Callable[[], None]):
        assert self.persistence_manager is not None
        self.persistence_manager.read_persisted(
            lambda persisted: (
                setattr(self, "user_payload", persisted),
                self._init(),
                complete_handler(),
            ),
            lambda: (self._init(), complete_handler()),
            file_name="UserPayload",
        )

    def _init(self):
        assert self.persistence_manager is not None
        self.persistence_manager.initialize(
            self.user_payload, PersistenceManagerSource.PRIVATE
        )

        assert (
            self.user_payload.payment_accounts is not None
        ), "userPayload.payment_accounts must not be null"
        assert (
            self.user_payload.accepted_language_locale_codes is not None
        ), "userPayload.accepted_language_locale_codes must not be null"

        self.payment_accounts_observable = ObservableSet["PaymentAccount"](
            self.user_payload.payment_accounts
        )
        self.current_payment_account_property.set(
            self.user_payload.current_payment_account
        )

        assert self.key_ring is not None
        self.user_payload.account_id = str(abs(hash(self.key_ring.pub_key_ring)))

        # Language setup
        if (
            LanguageUtil.get_default_language_locale_as_code()
            not in self.user_payload.accepted_language_locale_codes
        ):
            self.user_payload.accepted_language_locale_codes.append(
                LanguageUtil.get_default_language_locale_as_code()
            )
        english = LanguageUtil.get_english_language_locale_code()
        if english not in self.user_payload.accepted_language_locale_codes:
            self.user_payload.accepted_language_locale_codes.append(english)

        def on_payment_accounts_change(e: ObservableChangeEvent["PaymentAccount"]):
            self.user_payload.payment_accounts = set(self.payment_accounts_observable)
            self.request_persistence()

        self.payment_accounts_observable.add_listener(on_payment_accounts_change)

        def on_current_payment_account_change(
            value: "SimplePropertyChangeEvent[PaymentAccount]",
        ):
            self.user_payload.current_payment_account = value.new_value
            self.request_persistence()

        self.current_payment_account_property.add_listener(
            on_current_payment_account_change
        )

        # We create a default placeholder account for BSQ swaps. The account has not content, it is just used
        # so that the BsqSwap use case fits into the current domain
        self.add_bsq_swap_account()

        self.request_persistence()

    def add_bsq_swap_account(self):
        assert (
            self.user_payload.payment_accounts is not None
        ), "userPayload.payment_accounts must not be null"

        # Check if BsqSwapAccount already exists
        if any(
            isinstance(account, BsqSwapAccount)
            for account in self.user_payload.payment_accounts
        ):
            return

        account = BsqSwapAccount()
        account.init()
        account.account_name = Res.get("BSQ_SWAP")
        account.set_single_trade_currency(CryptoCurrency("BSQ", "BSQ"))
        self.add_payment_account(account)

    def request_persistence(self):
        if self.persistence_manager is not None:
            self.persistence_manager.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_accepted_arbitrator_by_address(
        self, node_address: "NodeAddress"
    ) -> Optional["Arbitrator"]:
        accepted_arbitrators = self.user_payload.accepted_arbitrators
        if accepted_arbitrators is not None:
            return next(
                (
                    arbitrator
                    for arbitrator in accepted_arbitrators
                    if arbitrator.node_address == node_address
                ),
                None,
            )
        return None

    def get_accepted_mediator_by_address(
        self, node_address: "NodeAddress"
    ) -> Optional["Mediator"]:
        accepted_mediators = self.user_payload.accepted_mediators
        if accepted_mediators is not None:
            return next(
                (
                    mediator
                    for mediator in accepted_mediators
                    if mediator.node_address == node_address
                ),
                None,
            )
        return None

    def get_accepted_refund_agent_by_address(
        self, node_address: "NodeAddress"
    ) -> Optional["RefundAgent"]:
        accepted_refund_agents = self.user_payload.accepted_refund_agents
        if accepted_refund_agents is not None:
            return next(
                (
                    agent
                    for agent in accepted_refund_agents
                    if agent.node_address == node_address
                ),
                None,
            )
        return None

    def find_first_payment_account_with_currency(
        self, trade_currency: "TradeCurrency"
    ) -> Optional["PaymentAccount"]:
        if self.user_payload.payment_accounts is not None:
            for payment_account in self.user_payload.payment_accounts:
                for currency in payment_account.trade_currencies:
                    if currency == trade_currency:
                        return payment_account
            return None
        else:
            return None

    def has_payment_account_for_currency(self, trade_currency: "TradeCurrency") -> bool:
        return self.find_first_payment_account_with_currency(trade_currency) is not None

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Collection operations
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_payment_account_if_not_exists(self, payment_account: "PaymentAccount"):
        if not self.payment_account_exists(payment_account):
            self.add_payment_account(payment_account)

    def add_payment_account(self, payment_account: "PaymentAccount"):
        payment_account.on_add_to_user()

        changed = self.payment_accounts_observable.add(payment_account)
        self.set_current_payment_account(payment_account)
        if changed:
            self.request_persistence()

    def add_imported_payment_accounts(self, payment_accounts: list["PaymentAccount"]):
        self.is_payment_account_import = True

        changed = self.payment_accounts_observable.update(payment_accounts)

        if payment_accounts:  # if list is not empty
            self.current_payment_account_property.set(payment_accounts[0])

        if changed:
            self.request_persistence()

        self.is_payment_account_import = False

    def remove_payment_account(self, payment_account: "PaymentAccount"):
        changed = self.payment_accounts_observable.discard(payment_account)
        if changed:
            self.request_persistence()

    def add_accepted_arbitrator(self, arbitrator: "Arbitrator") -> bool:
        arbitrators = self.user_payload.accepted_arbitrators
        if (
            arbitrators is not None
            and arbitrator not in arbitrators
            and not self.is_my_own_registered_arbitrator(arbitrator)
        ):
            arbitrators.append(arbitrator)
            self.request_persistence()
            return True
        return False

    def remove_accepted_arbitrator(self, arbitrator: "Arbitrator"):
        if self.user_payload.accepted_arbitrators is not None:
            try:
                self.user_payload.accepted_arbitrators.remove(arbitrator)
                self.request_persistence()
            except ValueError:
                pass

    def clear_accepted_arbitrators(self):
        if self.user_payload.accepted_arbitrators is not None:
            self.user_payload.accepted_arbitrators.clear()
            self.request_persistence()

    def add_accepted_mediator(self, mediator: "Mediator") -> bool:
        mediators = self.user_payload.accepted_mediators
        if (
            mediators is not None
            and mediator not in mediators
            and not self.is_my_own_registered_mediator(mediator)
        ):
            mediators.append(mediator)
            self.request_persistence()
            return True
        return False

    def remove_accepted_mediator(self, mediator: "Mediator"):
        if self.user_payload.accepted_mediators is not None:
            try:
                self.user_payload.accepted_mediators.remove(mediator)
                self.request_persistence()
            except ValueError:
                pass

    def clear_accepted_mediators(self):
        if self.user_payload.accepted_mediators is not None:
            self.user_payload.accepted_mediators.clear()
            self.request_persistence()

    def add_accepted_refund_agent(self, refund_agent: "RefundAgent") -> bool:
        refund_agents = self.user_payload.accepted_refund_agents
        if (
            refund_agents is not None
            and refund_agent not in refund_agents
            and not self.is_my_own_registered_refund_agent(refund_agent)
        ):
            refund_agents.append(refund_agent)
            self.request_persistence()
            return True
        return False

    def remove_accepted_refund_agent(self, refund_agent: "RefundAgent"):
        if self.user_payload.accepted_refund_agents is not None:
            try:
                self.user_payload.accepted_refund_agents.remove(refund_agent)
                self.request_persistence()
            except ValueError:
                pass

    def clear_accepted_refund_agents(self):
        if self.user_payload.accepted_refund_agents is not None:
            self.user_payload.accepted_refund_agents.clear()
            self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Setters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def set_current_payment_account(self, payment_account: "PaymentAccount"):
        self.current_payment_account_property.set(payment_account)
        self.request_persistence()

    def set_registered_arbitrator(self, arbitrator: Optional["Arbitrator"]):
        self.user_payload.registered_arbitrator = arbitrator
        self.request_persistence()

    def set_registered_mediator(self, mediator: Optional["Mediator"]):
        self.user_payload.registered_mediator = mediator
        self.request_persistence()

    def set_registered_refund_agent(self, refund_agent: Optional["RefundAgent"]):
        self.user_payload.registered_refund_agent = refund_agent
        self.request_persistence()

    def set_developers_filter(self, developers_filter: Optional["Filter"]):
        self.user_payload.developers_filter = developers_filter
        self.request_persistence()

    def set_developers_alert(self, developers_alert: Optional["Alert"]):
        self.user_payload.developers_alert = developers_alert
        self.request_persistence()

    def set_displayed_alert(self, displayed_alert: Optional["Alert"]):
        self.user_payload.displayed_alert = displayed_alert
        self.request_persistence()

    def add_market_alert_filter(self, filter: "MarketAlertFilter"):
        self.market_alert_filters.append(filter)
        self.request_persistence()

    def remove_market_alert_filter(self, filter: "MarketAlertFilter"):
        try:
            self.market_alert_filters.remove(filter)
            self.request_persistence()
        except:
            pass

    def set_price_alert_filter(self, filter: Optional["PriceAlertFilter"]):
        self.user_payload.price_alert_filter = filter
        self.request_persistence()

    def remove_price_alert_filter(self):
        self.user_payload.price_alert_filter = None
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_payment_account(
        self, payment_account_id: str
    ) -> Optional["PaymentAccount"]:
        if self.user_payload.payment_accounts is not None:
            return next(
                (
                    account
                    for account in self.user_payload.payment_accounts
                    if account.id == payment_account_id
                ),
                None,
            )
        return None

    @property
    def account_id(self) -> str:
        return self.user_payload.account_id

    @property
    def payment_accounts(self) -> Optional[set["PaymentAccount"]]:
        return self.user_payload.payment_accounts

    @property
    def registered_arbitrator(self) -> Optional["Arbitrator"]:
        """
        If this user is an arbitrator it returns the registered arbitrator.

        Returns:
            The arbitrator registered for this user
        """
        return self.user_payload.registered_arbitrator

    @property
    def registered_mediator(self) -> Optional["Mediator"]:
        return self.user_payload.registered_mediator

    @property
    def registered_refund_agent(self) -> Optional["RefundAgent"]:
        return self.user_payload.registered_refund_agent

    @property
    def accepted_arbitrators(self) -> Optional[list["Arbitrator"]]:
        return self.user_payload.accepted_arbitrators

    @property
    def accepted_mediators(self) -> Optional[list["Mediator"]]:
        return self.user_payload.accepted_mediators

    @property
    def accepted_refund_agents(self) -> Optional[list["RefundAgent"]]:
        return self.user_payload.accepted_refund_agents

    @property
    def accepted_arbitrator_addresses(self) -> Optional[list["NodeAddress"]]:
        if self.user_payload.accepted_arbitrators is not None:
            return [
                arbitrator.node_address
                for arbitrator in self.user_payload.accepted_arbitrators
            ]
        return None

    @property
    def accepted_mediator_addresses(self) -> Optional[list["NodeAddress"]]:
        if self.user_payload.accepted_mediators is not None:
            return [
                mediator.node_address
                for mediator in self.user_payload.accepted_mediators
            ]
        return None

    @property
    def accepted_refund_agent_addresses(self) -> Optional[list["NodeAddress"]]:
        if self.user_payload.accepted_refund_agents is not None:
            return [
                agent.node_address for agent in self.user_payload.accepted_refund_agents
            ]
        return None

    @property
    def has_accepted_arbitrators(self) -> bool:
        return (
            self.accepted_arbitrators is not None and len(self.accepted_arbitrators) > 0
        )

    @property
    def has_accepted_mediators(self) -> bool:
        return self.accepted_mediators is not None and len(self.accepted_mediators) > 0

    @property
    def has_accepted_refund_agents(self) -> bool:
        return (
            self.accepted_refund_agents is not None
            and len(self.accepted_refund_agents) > 0
        )

    @property
    def developers_filter(self) -> Optional["Filter"]:
        return self.user_payload.developers_filter

    @property
    def developers_alert(self) -> Optional["Alert"]:
        return self.user_payload.developers_alert

    @property
    def displayed_alert(self) -> Optional["Alert"]:
        return self.user_payload.displayed_alert

    def is_my_own_registered_arbitrator(self, arbitrator: "Arbitrator") -> bool:
        return arbitrator == self.user_payload.registered_arbitrator

    def is_my_own_registered_mediator(self, mediator: "Mediator") -> bool:
        return mediator == self.user_payload.registered_mediator

    def is_my_own_registered_refund_agent(self, refund_agent: "RefundAgent") -> bool:
        return refund_agent == self.user_payload.registered_refund_agent

    @property
    def market_alert_filters(self) -> list["MarketAlertFilter"]:
        return self.user_payload.market_alert_filters

    @property
    def price_alert_filter(self) -> Optional["PriceAlertFilter"]:
        return self.user_payload.price_alert_filter

    def payment_account_exists(self, payment_account: "PaymentAccount") -> bool:
        return payment_account in self.payment_accounts_observable

    @property
    def cookie(self) -> "Cookie":
        return self.user_payload.cookie

    @property
    def sub_accounts_by_id(self) -> dict[str, set["PaymentAccount"]]:
        return self.user_payload.sub_accounts_by_id
