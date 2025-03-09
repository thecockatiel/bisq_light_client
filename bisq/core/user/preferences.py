from collections.abc import Callable
import random
import re
from typing import TYPE_CHECKING, Optional
from bisq.common.config.base_currency_network import BaseCurrencyNetwork
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import get_system_home_directory
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.locale.country import Country
from bisq.core.locale.country_util import get_default_country
from bisq.core.locale.currency_util import get_currency_by_country_code, get_main_crypto_currencies, get_main_fiat_currencies
from bisq.core.locale.global_settings import GlobalSettings
from bisq.core.locale.locale_util import find_locale
from bisq.core.network.p2p.network.bridge_address_provider import BridgeAddressProvider
from bisq.core.payment.payment_account_util import PaymentAccountUtil
from bisq.core.provider.fee.fee_service import FeeService
from bisq.core.setup.core_network_capabilities import CoreNetworkCapabilities
from bisq.core.user.auto_confirm_settings import AutoConfirmSettings
from bisq.core.user.dont_show_again_lookup import DontShowAgainLookup
from bisq.core.user.preferences_const import (
    BSQ_MAIN_NET_EXPLORERS,
    BTC_DAO_TEST_NET_EXPLORERS,
    BTC_MAIN_NET_EXPLORERS,
    BTC_TEST_NET_EXPLORERS,
    CLEAR_DATA_AFTER_DAYS_INITIAL,
    TX_BROADCAST_SERVICES,
    TX_BROADCAST_SERVICES_CLEAR_NET,
    XMR_TX_PROOF_SERVICES,
    XMR_TX_PROOF_SERVICES_CLEAR_NET,
)
from bisq.core.user.block_chain_explorer import BlockChainExplorer
from bisq.core.user.preferences_payload import PreferencesPayload 
from utils.data import ObservableChangeEvent, ObservableList, ObservableMap, SimpleProperty, SimplePropertyChangeEvent

if TYPE_CHECKING:
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.common.config.config import Config
    from bisq.core.locale.crypto_currency import CryptoCurrency
    from bisq.core.locale.trade_currency import TradeCurrency
    from bisq.core.locale.fiat_currency import FiatCurrency

logger = get_logger(__name__)

# NOTE: Keep up to date with https://github.com/bisq-network/bisq/blob/v1.9.19/core/src/main/java/bisq/core/user/Preferences.java
# removed LocalBitcoinNode
# replaced unsupported options with constants

class Preferences(PersistedDataHost, BridgeAddressProvider):

    def __init__(
        self,
        persistence_manager: "PersistenceManager[PreferencesPayload]",
        config: "Config",
        fee_service: "FeeService",
    ) -> None:
        super().__init__()
        self.persistence_manager = persistence_manager
        self.config = config
        self.fee_service = fee_service
        self.btc_nodes_from_options = config.btc_nodes
        self.referral_id_from_options = config.referral_id
        self.full_dao_node_from_options = config.full_dao_node
        self.full_accounting_node_from_options = config.is_bm_full_node
        self.use_full_mode_dao_monitor_from_options = config.use_full_mode_dao_monitor
        self.rpc_user_from_options = config.rpc_user
        self.rpc_pw_from_options = config.rpc_password
        self.block_notify_port_from_options = config.rpc_block_notification_port
        
        ###### fields
        # payload is initialized so the default values are available for Property initialization.
        self.pref_payload = PreferencesPayload()
        self.initial_read_done = False
        
        self.use_animations_property = SimpleProperty(self.pref_payload.use_animations)
        self.css_theme_property = SimpleProperty(self.pref_payload.css_theme)
        
        self.fiat_currencies_as_observable = ObservableList["FiatCurrency"]()
        self.crypto_currencies_as_observable = ObservableList["CryptoCurrency"]()
        self.trade_currencies_as_observable = ObservableList["TradeCurrency"]()
        self.dont_show_again_map_as_observable = ObservableMap[str, bool]()
        
        self.use_standby_mode_property = SimpleProperty(self.pref_payload.use_standby_mode)
        
        ###### init
        def on_use_animation_change(e: SimplePropertyChangeEvent[bool]):
            self.pref_payload.use_animations = e.new_value
            GlobalSettings.use_animations = e.new_value
            self.request_persistence()
        self.use_animations_property.add_listener(on_use_animation_change)
        
        def on_css_theme_change(e: SimplePropertyChangeEvent[int]):
            self.pref_payload.css_theme = e.new_value
            self.request_persistence()
        self.css_theme_property.add_listener(on_css_theme_change)
        
        def on_use_standby_change(e: SimplePropertyChangeEvent[int]):
            self.pref_payload.use_standby_mode = e.new_value
            self.request_persistence()
        self.use_standby_mode_property.add_listener(on_use_standby_change)
        
        def on_fiat_currencies_change(e):
            self.pref_payload.fiat_currencies.clear()
            self.pref_payload.fiat_currencies.extend(self.fiat_currencies_as_observable)
            self.pref_payload.fiat_currencies.sort(key=lambda x: x.name)
            self.request_persistence()
        self.fiat_currencies_as_observable.add_listener(on_fiat_currencies_change)
        
        def on_crypto_currencies_change(e):
            self.pref_payload.crypto_currencies.clear()
            self.pref_payload.crypto_currencies.extend(self.crypto_currencies_as_observable)
            self.pref_payload.crypto_currencies.sort(key=lambda x: x.name)
            self.request_persistence()
        self.crypto_currencies_as_observable.add_listener(on_crypto_currencies_change)
        
        self.fiat_currencies_as_observable.add_listener(self.update_trade_currencies)
        self.crypto_currencies_as_observable.add_listener(self.update_trade_currencies)
        
    def read_persisted(self, complete_handler: Callable[[], None]) -> None:
        def result_handler(persisted: "PreferencesPayload"):
            self._init_from_persisted_preferences(persisted)
            complete_handler()
        def or_else():
            self._init_new_preferences()
            complete_handler()
        self.persistence_manager.read_persisted(result_handler, or_else, file_name="PreferencesPayload")
        
    def _init_from_persisted_preferences(self, persisted: "PreferencesPayload"):
        self.pref_payload = persisted
        GlobalSettings.locale_property.value = find_locale(self.pref_payload.user_language, self.pref_payload.user_country.code)
        GlobalSettings.use_animations = self.pref_payload.use_animations
        assert self.pref_payload.preferred_trade_currency, "preferred_trade_currency must have a value"
        preferred_trade_currency = self.pref_payload.preferred_trade_currency
        self.set_preferred_trade_currency(preferred_trade_currency)
        self.set_fiat_currencies(self.pref_payload.fiat_currencies)
        self.set_crypto_currencies(self.pref_payload.crypto_currencies)
        self.set_bsq_blockchain_explorer(self.pref_payload.bsq_block_chain_explorer)
        GlobalSettings.default_trade_currency = preferred_trade_currency

        # If a user has updated and the field was not set and get set to 0 by protobuf
        # As there is no way to detect that a primitive value field was set we cannot apply
        # a "marker" value like -1 to it. We also do not want to wrap the value in a new
        # proto message as thats too much for that feature... So we accept that if the user
        # sets the value to 0 it will be overwritten by the default at next startup.
        if self.pref_payload.bsq_average_trim_threshold == 0:
            self.pref_payload.bsq_average_trim_threshold = 0.05

        self._setup_preferences()
    
    def _init_new_preferences(self):
        self.pref_payload = PreferencesPayload()
        self.pref_payload.user_language = GlobalSettings.locale_property.value.language
        self.pref_payload.user_country = get_default_country()
        GlobalSettings.locale_property.value = find_locale(
            self.pref_payload.user_language, 
            self.pref_payload.user_country.code
        )

        preferred_trade_currency = get_currency_by_country_code("US")  # default fallback
        try:
            preferred_trade_currency = get_currency_by_country_code(
                self.pref_payload.user_country.code
            )
        except ValueError as e:
            logger.warning(
                f"Could not determine currency for country {self.pref_payload.user_country.code}: {str(e)}"
            )

        self.pref_payload.preferred_trade_currency = preferred_trade_currency
        self.set_fiat_currencies(get_main_fiat_currencies())
        self.set_crypto_currencies(get_main_crypto_currencies())

        base_currency_network = self.config.base_currency_network
        if base_currency_network.currency_code == "BTC":
            self.set_blockchain_explorer_main_net(BTC_MAIN_NET_EXPLORERS[0])
            self.set_blockchain_explorer_test_net(BTC_TEST_NET_EXPLORERS[0])
        else:
            raise RuntimeError(f"base_currency_network not defined. base_currency_network={base_currency_network}")

        self.pref_payload.directory_chooser_path = str(get_system_home_directory())

        self.pref_payload.offer_book_chart_screen_currency_code = preferred_trade_currency.code
        self.pref_payload.trade_charts_screen_currency_code = preferred_trade_currency.code
        self.pref_payload.buy_screen_currency_code = preferred_trade_currency.code
        self.pref_payload.sell_screen_currency_code = preferred_trade_currency.code
        GlobalSettings.default_trade_currency = preferred_trade_currency
        self._setup_preferences()
    
    def _setup_preferences(self):
        self.persistence_manager.initialize(self.pref_payload, PersistenceManagerSource.PRIVATE)
        
        # We don't want to pass Preferences to all popups where the don't show again checkbox is used, so we use
        # that static lookup class to avoid static access to the Preferences directly.
        DontShowAgainLookup.set_preferences(self)
        
        # set all properties
        self.use_animations_property.value = self.pref_payload.use_animations
        self.use_standby_mode_property.value = self.pref_payload.use_standby_mode
        self.css_theme_property.value = self.pref_payload.css_theme
        
        self._clear_retired_nodes()
        
        # Set trade currencies
        self.trade_currencies_as_observable.extend(self.pref_payload.fiat_currencies)
        self.trade_currencies_as_observable.extend(self.pref_payload.crypto_currencies)
        self.dont_show_again_map_as_observable.update(self.pref_payload.dont_show_again_map)
        
        # Override settings with options if set
        if self.config.use_tor_for_btc_option_set_explicitly:
            self.set_use_tor_for_bitcoin_j(self.config.use_tor_for_btc)
    
        if self.btc_nodes_from_options:
            # we don't care about btc nodes from options
            pass
        
        if self.referral_id_from_options:
            self.set_referral_id(self.referral_id_from_options)
        

        if self.pref_payload.ignore_dust_threshold < Restrictions.get_min_non_dust_output().value:
            self.set_ignore_dust_threshold(600)
        
        # Set minimum clear data days
        if self.pref_payload.clear_data_after_days < 1:
            self.set_clear_data_after_days(CLEAR_DATA_AFTER_DAYS_INITIAL)
        
        # For users from old versions the 4 flags a false but we want to have it true by default
        # PhoneKeyAndToken is also null so we can use that to enable the flags
        if self.pref_payload.phone_key_and_token is None:
            self.set_use_sound_for_mobile_notifications(True)
            self.set_use_trade_notifications(True)
            self.set_use_market_notifications(True)
            self.set_use_price_notifications(True)
        
        # We set the capability in CoreNetworkCapabilities if the program argument is set.
        # If we have set it in the preferences view we handle it here.
        CoreNetworkCapabilities.maybe_apply_dao_full_mode(self.config)
        
        self.initial_read_done = True
        self.request_persistence()

    def _clear_retired_nodes(self):
        # a list of previously-used federated explorers    
        # if user preference references any deprecated explorers we need to select a new valid explorer
        deprecated_explorers = re.compile(r"(bsq.bisq.cc|bsq.vante.me|bsq.emzy.de|bsq.sqrrm.net|bsq.bisq.services|bsq.ninja|bisq.mempool.emzy.de).*")

        # if no valid Bitcoin block explorer is set, select the 1st valid Bitcoin block explorer
        btc_explorers = self.get_block_chain_explorers()
        if (self.get_block_chain_explorer() is None or
                not self.get_block_chain_explorer().name or
                deprecated_explorers.match(self.get_block_chain_explorer().name)):
            self.set_block_chain_explorer(btc_explorers[0])

        # if no valid BSQ block explorer is set, randomly select a valid BSQ block explorer
        bsq_explorers = self.get_bsq_block_chain_explorers()
        if (self.get_bsq_block_chain_explorer() is None or
                not self.get_bsq_block_chain_explorer().name or
                deprecated_explorers.match(self.get_bsq_block_chain_explorer().name)):
            self.set_bsq_blockchain_explorer(random.choice(bsq_explorers))

        # Remove retired XMR AutoConfirm addresses
        retired_addresses = [
            "monero3bec7m26vx6si6qo7q7imlaoz45ot5m2b5z2ppgoooo6jx2rqd",
            "devinxmrwu4jrfq2zmq5kqjpxb44hx7i7didebkwrtvmvygj4uuop2ad"
        ]
        # TODO: java sanity check later
        do_apply_defaults = any(
            any(retired_address in address for address in auto_confirm_settings.service_addresses)
            for auto_confirm_settings in self.pref_payload.auto_confirm_settings_list
            for retired_address in retired_addresses
        )
        if do_apply_defaults:
            self.pref_payload.auto_confirm_settings_list.clear()
            default_xmr_tx_proof_services = self.get_default_xmr_tx_proof_services()
            xmr_auto_confirm_settings = AutoConfirmSettings.get_default(default_xmr_tx_proof_services, "XMR")
            if xmr_auto_confirm_settings:
                self.pref_payload.auto_confirm_settings_list.append(xmr_auto_confirm_settings)
            self.persistence_manager.force_persist_now()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def dont_show_again(self, key: str, dont_show_again: bool):
        self.pref_payload.dont_show_again_map[key] = dont_show_again
        self.request_persistence()
        self.dont_show_again_map_as_observable[key] = dont_show_again
        
    def reset_dont_show_again(self):
        self.pref_payload.dont_show_again_map.clear()
        self.dont_show_again_map_as_observable.clear()
        self.request_persistence()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Setter
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def set_css_theme(self, use_dark_mode: bool):
        self.css_theme_property.value = 1 if use_dark_mode else 0

    def add_fiat_currency(self, trade_currency: "FiatCurrency") -> None:
        if trade_currency not in self.fiat_currencies_as_observable:
            self.fiat_currencies_as_observable.append(trade_currency)

    def remove_fiat_currency(self, trade_currency: "FiatCurrency") -> None:
        if len(self.trade_currencies_as_observable) > 1:
            if trade_currency in self.fiat_currencies_as_observable:
                self.fiat_currencies_as_observable.remove(trade_currency)

            if (self.pref_payload.preferred_trade_currency and 
                self.pref_payload.preferred_trade_currency == trade_currency):
                self.set_preferred_trade_currency(self.trade_currencies_as_observable[0])
        else:
            logger.error("you cannot remove the last currency")

    def add_crypto_currency(self, trade_currency: "CryptoCurrency") -> None:
        if trade_currency not in self.crypto_currencies_as_observable:
            self.crypto_currencies_as_observable.append(trade_currency)

    def remove_crypto_currency(self, trade_currency: "CryptoCurrency") -> None:
        if len(self.trade_currencies_as_observable) > 1:
            if trade_currency in self.crypto_currencies_as_observable:
                self.crypto_currencies_as_observable.remove(trade_currency)

            if (self.pref_payload.preferred_trade_currency and 
                self.pref_payload.preferred_trade_currency == trade_currency):
                self.set_preferred_trade_currency(self.trade_currencies_as_observable[0])
        else:
            logger.error("you cannot remove the last currency")

    def set_block_chain_explorer(self, block_chain_explorer: "BlockChainExplorer") -> None:
        if self.config.base_currency_network.is_mainnet():
            self.set_blockchain_explorer_main_net(block_chain_explorer)
        else:
            self.set_blockchain_explorer_test_net(block_chain_explorer)

    def set_tac_accepted(self, tac_accepted: bool) -> None:
        self.pref_payload.tac_accepted = tac_accepted
        self.request_persistence()

    def set_tac_accepted_v120(self, tac_accepted: bool) -> None:
        self.pref_payload.tac_accepted_v120 = tac_accepted
        self.request_persistence()

    def set_bsq_average_trim_threshold(self, value: float) -> None:
        self.pref_payload.bsq_average_trim_threshold = value
        self.request_persistence()
            
    def find_auto_confirm_settings(self, currency_code: str) -> Optional["AutoConfirmSettings"]:
        return next(
            (e for e in self.pref_payload.auto_confirm_settings_list if e.currency_code == currency_code),
            None
        )
    
    def set_auto_conf_service_addresses(self, currency_code: str, service_addresses: list[str]) -> None:
        settings = self.find_auto_confirm_settings(currency_code)
        if settings:
            settings.service_addresses = service_addresses
            self.request_persistence()
    
    def set_auto_conf_enabled(self, currency_code: str, enabled: bool) -> None:
        settings = self.find_auto_confirm_settings(currency_code)
        if settings:
            settings.enabled = enabled
            self.request_persistence()
    
    def set_auto_conf_required_confirmations(self, currency_code: str, required_confirmations: int) -> None:
        settings = self.find_auto_confirm_settings(currency_code)
        if settings:
            settings.required_confirmations = required_confirmations
            self.request_persistence()
    
    def set_auto_conf_trade_limit(self, currency_code: str, trade_limit: int) -> None:
        settings = self.find_auto_confirm_settings(currency_code)
        if settings:
            settings.trade_limit = trade_limit
            self.request_persistence()
    
    def set_hide_non_account_payment_methods(self, hide_non_account_payment_methods: bool) -> None:
        self.pref_payload.hide_non_account_payment_methods = hide_non_account_payment_methods
        self.request_persistence()

    def request_persistence(self):
        if self.initial_read_done:  
            self.persistence_manager.request_persistence()
            
    def set_user_language(self, user_language_code: str) -> None:
        assert user_language_code
        self.pref_payload.user_language = user_language_code
        if self.pref_payload.user_country and self.pref_payload.user_language:
            GlobalSettings.locale_property.value = find_locale(
                self.pref_payload.user_language,
                self.pref_payload.user_country.code
            )
        self.request_persistence()

    def set_user_country(self, user_country: "Country") -> None:
        assert user_country
        self.pref_payload.user_country = user_country
        if self.pref_payload.user_language:
            GlobalSettings.locale_property.value = find_locale(
                self.pref_payload.user_language,
                user_country.code
            )
        self.request_persistence()

    def set_preferred_trade_currency(self, preferred_trade_currency: "TradeCurrency") -> None:
        if preferred_trade_currency:
            self.pref_payload.preferred_trade_currency = preferred_trade_currency
            GlobalSettings.default_trade_currency = preferred_trade_currency
            self.request_persistence()

    def set_use_tor_for_bitcoin_j(self, use_tor_for_bitcoin_j: bool) -> None:
        self.pref_payload.use_tor_for_bitcoin_j = use_tor_for_bitcoin_j
        self.request_persistence()

    def set_show_own_offers_in_offer_book(self, show_own_offers_in_offer_book: bool) -> None:
        self.pref_payload.show_own_offers_in_offer_book = show_own_offers_in_offer_book
        self.request_persistence()

    def set_max_price_distance_in_percent(self, max_price_distance_in_percent: float) -> None:
        self.pref_payload.max_price_distance_in_percent = max_price_distance_in_percent
        self.request_persistence()

    def set_backup_directory(self, backup_directory: str) -> None:
        self.pref_payload.backup_directory = backup_directory
        self.request_persistence()

    def set_auto_select_arbitrators(self, auto_select_arbitrators: bool) -> None:
        self.pref_payload.auto_select_arbitrators = auto_select_arbitrators
        self.request_persistence()

    def set_use_percentage_based_price(self, use_percentage_based_price: bool) -> None:
        self.pref_payload.use_percentage_based_price = use_percentage_based_price
        self.request_persistence()

    def set_tag_for_peer(self, full_address: str, tag: str) -> None:
        self.pref_payload.peer_tag_map[full_address] = tag
        self.request_persistence()

    def set_offer_book_chart_screen_currency_code(self, currency_code: str) -> None:
        self.pref_payload.offer_book_chart_screen_currency_code = currency_code
        self.request_persistence()

    def set_buy_screen_currency_code(self, buy_screen_currency_code: str) -> None:
        self.pref_payload.buy_screen_currency_code = buy_screen_currency_code
        self.request_persistence()

    def set_sell_screen_currency_code(self, sell_screen_currency_code: str) -> None:
        self.pref_payload.sell_screen_currency_code = sell_screen_currency_code
        self.request_persistence()

    def set_buy_screen_crypto_currency_code(self, buy_screen_currency_code: str) -> None:
        self.pref_payload.buy_screen_crypto_currency_code = buy_screen_currency_code
        self.request_persistence()

    def set_sell_screen_crypto_currency_code(self, sell_screen_currency_code: str) -> None:
        self.pref_payload.sell_screen_crypto_currency_code = sell_screen_currency_code
        self.request_persistence()

    def set_ignore_traders_list(self, ignore_traders_list: list[str]) -> None:
        self.pref_payload.ignore_traders_list = ignore_traders_list
        self.request_persistence()

    def set_directory_chooser_path(self, directory_chooser_path: str) -> None:
        self.pref_payload.directory_chooser_path = directory_chooser_path
        self.request_persistence()

    def set_trade_charts_screen_currency_code(self, trade_charts_screen_currency_code: str) -> None:
        self.pref_payload.trade_charts_screen_currency_code = trade_charts_screen_currency_code
        self.request_persistence()

    def set_trade_statistics_tick_unit_index(self, trade_statistics_tick_unit_index: int) -> None:
        self.pref_payload.trade_statistics_tick_unit_index = trade_statistics_tick_unit_index
        self.request_persistence()

    def set_sort_market_currencies_numerically(self, sort_market_currencies_numerically: bool) -> None:
        self.pref_payload.sort_market_currencies_numerically = sort_market_currencies_numerically
        self.request_persistence()
        
    def set_bitcoin_nodes(self, bitcoin_nodes: str) -> None:
        self.pref_payload.bitcoin_nodes = bitcoin_nodes
        self.request_persistence()

    def set_use_custom_withdrawal_tx_fee(self, use_custom_withdrawal_tx_fee: bool) -> None:
        self.pref_payload.use_custom_withdrawal_tx_fee = use_custom_withdrawal_tx_fee
        self.request_persistence()

    def set_withdrawal_tx_fee_in_vbytes(self, withdrawal_tx_fee_in_vbytes: int) -> None:
        self.pref_payload.withdrawal_tx_fee_in_vbytes = withdrawal_tx_fee_in_vbytes
        self.request_persistence()

    def set_buyer_security_deposit_as_percent(self, buyer_security_deposit_as_percent: float, payment_account: "PaymentAccount") -> None:
        max_deposit = Restrictions.get_max_buyer_security_deposit_as_percent()
        min_deposit = Restrictions.get_min_buyer_security_deposit_as_percent()
        
        clamped_deposit = min(max_deposit, max(min_deposit, buyer_security_deposit_as_percent))
        
        if PaymentAccountUtil.is_cryptocurrency_account(payment_account):
            self.pref_payload.buyer_security_deposit_as_percent_for_crypto = clamped_deposit
        else:
            self.pref_payload.buyer_security_deposit_as_percent = clamped_deposit
        self.request_persistence()

    def set_selected_payment_account_for_create_offer(self, payment_account: Optional["PaymentAccount"]) -> None:
        self.pref_payload.selected_payment_account_for_create_offer = payment_account
        self.request_persistence()

    def set_pay_fee_in_btc(self, pay_fee_in_btc: bool) -> None:
        self.pref_payload.pay_fee_in_btc = pay_fee_in_btc
        self.request_persistence()
    
    def set_fiat_currencies(self, currencies: list["FiatCurrency"]) -> None:
        from bisq.core.locale.fiat_currency import FiatCurrency
        unique_currencies = {FiatCurrency(curr.currency) for curr in currencies}
        self.fiat_currencies_as_observable.clear()
        self.fiat_currencies_as_observable.extend(list(unique_currencies))
        self.request_persistence()
    
    def set_crypto_currencies(self, currencies: list["CryptoCurrency"]) -> None:
        unique_currencies = list(set(currencies))
        self.crypto_currencies_as_observable.clear()
        self.crypto_currencies_as_observable.extend(unique_currencies)
        self.request_persistence()
        
    def set_bsq_blockchain_explorer(self, bsq_block_chain_explorer: "BlockChainExplorer") -> None:
        self.pref_payload.bsq_block_chain_explorer = bsq_block_chain_explorer
        self.request_persistence()
    
    def set_blockchain_explorer_test_net(self, blockchain_explorer_test_net: "BlockChainExplorer") -> None:
        self.pref_payload.block_chain_explorer_test_net = blockchain_explorer_test_net
        self.request_persistence()
    
    def set_blockchain_explorer_main_net(self, blockchain_explorer_main_net: "BlockChainExplorer") -> None:
        self.pref_payload.block_chain_explorer_main_net = blockchain_explorer_main_net
        self.request_persistence()
        
    def set_resync_spv_requested(self, requested: bool) -> None:
        self.pref_payload.resync_spv_requested = requested
        # We call that before shutdown so we dont want a delay here
        self.request_persistence()
        
    def set_bridge_addresses(self, addresses: list[str]) -> None:
        self.pref_payload.bridge_addresses = addresses
        # We call that before shutdown so we dont want a delay here
        self.persistence_manager.force_persist_now()
        
    # Only used from PB but keep it explicit as it may be used from the client and then we want to persist
    def set_peer_tag_map(self, peer_tag_map: dict[str, str]):
        self.pref_payload.peer_tag_map = peer_tag_map
        self.request_persistence()
        
    def set_bridge_option_ordinal(self, bridge_option_ordinal: int):
        self.pref_payload.bridge_option_ordinal = bridge_option_ordinal
        self.persistence_manager.force_persist_now()
        
    def set_tor_transport_ordinal(self, tor_transport_ordinal: int):
        self.pref_payload.tor_transport_ordinal = tor_transport_ordinal
        self.persistence_manager.force_persist_now()

    def set_custom_bridges(self, custom_bridges: str):
        self.pref_payload.custom_bridges = custom_bridges
        self.persistence_manager.force_persist_now()
                
    def set_bitcoin_nodes_option_ordinal(self, bitcoin_nodes_option_ordinal: int):
        self.pref_payload.bitcoin_nodes_option_ordinal = bitcoin_nodes_option_ordinal
        self.request_persistence()
        
    def set_referral_id(self, referral_id):
        self.pref_payload.referral_id = referral_id
        self.request_persistence()
        
    def set_phone_key_and_token(self, phone_key_and_token: Optional[str]) -> None:
        self.pref_payload.phone_key_and_token = phone_key_and_token
        self.request_persistence()

    def set_use_sound_for_mobile_notifications(self, value: bool) -> None:
        self.pref_payload.use_sound_for_mobile_notifications = value
        self.request_persistence()

    def set_use_trade_notifications(self, value: bool) -> None:
        self.pref_payload.use_trade_notifications = value
        self.request_persistence()

    def set_use_market_notifications(self, value: bool) -> None:
        self.pref_payload.use_market_notifications = value
        self.request_persistence()

    def set_use_price_notifications(self, value: bool) -> None:
        self.pref_payload.use_price_notifications = value
        self.request_persistence()

    def set_use_standby_mode(self, use_standby_mode: bool) -> None:
        self.use_standby_mode_property.value = use_standby_mode

    def set_take_offer_selected_payment_account_id(self, value: str) -> None:
        self.pref_payload.take_offer_selected_payment_account_id = value
        self.request_persistence()

    def set_dao_full_node(self, value: bool) -> None:
        # We only persist if we have not set the program argument
        if not self.config.full_dao_node_option_set_explicitly:
            self.pref_payload.is_dao_full_node = value
            self.request_persistence()

    def set_rpc_user(self, value: str) -> None:
        # We only persist if we have not set the program argument
        if not self.rpc_user_from_options:
            self.pref_payload.rpc_user = value
            self.request_persistence()

    def set_rpc_pw(self, value: str) -> None:
        # We only persist if we have not set the program argument
        if not self.rpc_pw_from_options:
            self.pref_payload.rpc_pw = value
            self.request_persistence()

    def set_block_notify_port(self, value: int) -> None:
        # We only persist if we have not set the program argument
        if self.block_notify_port_from_options == Config.UNSPECIFIED_PORT:
            self.pref_payload.block_notify_port = value
            self.request_persistence()
        
    def set_ignore_dust_threshold(self, value: int) -> None:
        self.pref_payload.ignore_dust_threshold = value
        self.request_persistence()
        
    def set_clear_data_after_days(self, value: int) -> None:
        self.pref_payload.clear_data_after_days = value
        self.request_persistence()
        
    def set_show_offers_matching_my_accounts(self, value: bool) -> None:
        self.pref_payload.show_offers_matching_my_accounts = value
        self.request_persistence()
        
    def set_deny_api_taker(self, value: bool) -> None:
        self.pref_payload.deny_api_taker = value
        self.request_persistence()
        
    def set_notify_on_pre_release(self, value: bool) -> None:
        self.pref_payload.notify_on_pre_release = value
        self.request_persistence()
        
    def set_use_full_mode_dao_monitor(self, value: bool) -> None:
        # We only persist if we have not set the program argument
        if not self.config.use_full_mode_dao_monitor_option_set_explicitly:
            self.pref_payload.use_full_mode_dao_monitor = value
            self.request_persistence()
        
    def set_use_bitcoin_uris_in_qr_codes(self, value: bool) -> None:
        self.pref_payload.use_bitcoin_uris_in_qr_codes = value 
        self.request_persistence()
        
    def set_user_has_raised_trade_limit(self, value: bool) -> None:
        self.pref_payload.user_has_raised_trade_limit = value
        self.request_persistence()
        
    def set_user_defined_trade_limit(self, value: int) -> None:
        self.pref_payload.user_defined_trade_limit = value
        self.request_persistence()
        
    def set_process_burning_man_accounting_data(self, process_burning_man_accounting_data: bool) -> None:
        self.pref_payload.process_burning_man_accounting_data = process_burning_man_accounting_data
        self.request_persistence()
        
    def set_full_bm_accounting_node(self, is_full_bm_accounting_node: bool) -> None:
        self.pref_payload.is_full_bm_accounting_node = is_full_bm_accounting_node
        self.request_persistence()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getter
    # ///////////////////////////////////////////////////////////////////////////////////////////
        
    def get_block_chain_explorer(self):
        base_currency_network = self.config.base_currency_network
        if base_currency_network == BaseCurrencyNetwork.BTC_MAINNET:
            return self.pref_payload.block_chain_explorer_main_net
        elif base_currency_network in [BaseCurrencyNetwork.BTC_TESTNET, BaseCurrencyNetwork.BTC_REGTEST]:
            return self.pref_payload.block_chain_explorer_test_net
        elif base_currency_network == BaseCurrencyNetwork.BTC_DAO_TESTNET:
            return BTC_DAO_TEST_NET_EXPLORERS[0]
        elif base_currency_network == BaseCurrencyNetwork.BTC_DAO_BETANET:
            return self.pref_payload.block_chain_explorer_main_net
        elif base_currency_network == BaseCurrencyNetwork.BTC_DAO_REGTEST:
            return BTC_DAO_TEST_NET_EXPLORERS[0]
        else:
            raise RuntimeError(f"BaseCurrencyNetwork not defined. BaseCurrencyNetwork={base_currency_network}")

    def get_block_chain_explorers(self):
        base_currency_network = self.config.base_currency_network
        if base_currency_network == BaseCurrencyNetwork.BTC_MAINNET:
            return BTC_MAIN_NET_EXPLORERS
        elif base_currency_network in [BaseCurrencyNetwork.BTC_TESTNET, BaseCurrencyNetwork.BTC_REGTEST]:
            return BTC_TEST_NET_EXPLORERS
        elif base_currency_network == BaseCurrencyNetwork.BTC_DAO_TESTNET:
            return BTC_DAO_TEST_NET_EXPLORERS
        elif base_currency_network == BaseCurrencyNetwork.BTC_DAO_BETANET:
            return BTC_MAIN_NET_EXPLORERS
        elif base_currency_network == BaseCurrencyNetwork.BTC_DAO_REGTEST:
            return BTC_DAO_TEST_NET_EXPLORERS
        else:
            raise RuntimeError(f"BaseCurrencyNetwork not defined. BaseCurrencyNetwork={base_currency_network}")

    def get_bsq_block_chain_explorers(self):
        return BSQ_MAIN_NET_EXPLORERS

    def get_bsq_block_chain_explorer(self):
        return self.pref_payload.bsq_block_chain_explorer
    
    def show_again(self, key: str):
        return key not in self.pref_payload.dont_show_again_map or not self.pref_payload.dont_show_again_map.get(key)

    def get_use_tor_for_bitcoin_j(self) -> bool:
        # We override the useTorForBitcoinJ and set it to false if we will use a
        # localhost Bitcoin node or if we are not on mainnet, unless the useTorForBtc
        # parameter is explicitly provided. On testnet there are very few Bitcoin tor
        # nodes and we don't provide tor nodes.
        
        if (not self.config.base_currency_network.is_mainnet() and
            not self.config.use_tor_for_btc_option_set_explicitly):
            return False
        else:
            return self.pref_payload.use_tor_for_bitcoin_j

    def get_buyer_security_deposit_as_percent(self, payment_account: "PaymentAccount") -> float:
        value = (self.pref_payload.buyer_security_deposit_as_percent_for_crypto 
                if PaymentAccountUtil.is_cryptocurrency_account(payment_account)
                else self.pref_payload.buyer_security_deposit_as_percent)

        if value < Restrictions.get_min_buyer_security_deposit_as_percent():
            value = Restrictions.get_min_buyer_security_deposit_as_percent()
            self.set_buyer_security_deposit_as_percent(value, payment_account)

        return (Restrictions.get_default_buyer_security_deposit_as_percent() 
                if value == 0 else value)
        
    def get_preferred_trade_currency(self):
        return self.pref_payload.preferred_trade_currency
    
    def get_user_country(self):
        return self.pref_payload.user_country

    def get_bridge_addresses(self) -> Optional[list[str]]:
        return self.pref_payload.bridge_addresses

    def get_withdrawal_tx_fee_in_vbytes(self) -> int:
        return max(self.pref_payload.withdrawal_tx_fee_in_vbytes,
                  self.fee_service.min_fee_per_vbyte)

    def is_dao_full_node(self) -> bool:
        if self.config.full_dao_node_option_set_explicitly:
            return self.full_dao_node_from_options
        else:
            return self.pref_payload.is_dao_full_node

    def get_rpc_user(self) -> str:
        if self.rpc_user_from_options:
            return self.rpc_user_from_options
        else:
            return self.pref_payload.rpc_user

    def get_rpc_pw(self) -> str:
        if self.rpc_pw_from_options:
            return self.rpc_pw_from_options
        else:
            return self.pref_payload.rpc_pw
        
    def get_clear_data_after_days(self):
        return self.pref_payload.clear_data_after_days

    def get_block_notify_port(self) -> int:
        if self.block_notify_port_from_options != Config.UNSPECIFIED_PORT:
            try:
                return self.block_notify_port_from_options
            except:
                return 0
        else:
            return self.pref_payload.block_notify_port

    def get_ignore_dust_threshold(self):
        return self.pref_payload.ignore_dust_threshold

    def get_default_xmr_tx_proof_services(self) -> list[str]:
        if self.config.use_localhost_for_p2p:
            return XMR_TX_PROOF_SERVICES_CLEAR_NET
        else:
            return XMR_TX_PROOF_SERVICES

    def get_default_tx_broadcast_services(self) -> list[str]:
        if self.config.use_localhost_for_p2p:
            return TX_BROADCAST_SERVICES_CLEAR_NET
        else:
            return TX_BROADCAST_SERVICES

    def is_process_burning_man_accounting_data(self) -> bool:
        return self.full_accounting_node_from_options or self.pref_payload.process_burning_man_accounting_data

    def is_full_bm_accounting_node(self) -> bool:
        return self.pref_payload.is_full_bm_accounting_node
    
    def is_use_full_mode_dao_monitor(self) -> bool:
        if self.config.use_full_mode_dao_monitor_option_set_explicitly:
            return self.use_full_mode_dao_monitor_from_options
        else:
            return self.pref_payload.use_full_mode_dao_monitor
    
    def is_notify_on_pre_release(self) -> bool:
        return self.pref_payload.notify_on_pre_release
    
    def get_user_has_raised_trade_limit(self):
        return self.pref_payload.user_has_raised_trade_limit
    
    def get_user_defined_trade_limit(self):
        return self.pref_payload.user_defined_trade_limit

    def is_pay_fee_in_btc(self) -> bool:
        return self.pref_payload.pay_fee_in_btc
    
    def get_auto_confirm_settings_list(self):
        return self.pref_payload.auto_confirm_settings_list
    
    def get_use_custom_withdrawal_tx_fee(self):
        return self.pref_payload.use_custom_withdrawal_tx_fee
    
    def get_ignore_traders_list(self):
        return self.pref_payload.ignore_traders_list
    
    def is_deny_api_taker(self):
        return self.pref_payload.deny_api_taker
    
    def get_referral_id(self):
        return self.pref_payload.referral_id
    
    def get_phone_key_and_token(self):
        return self.pref_payload.phone_key_and_token
    
    def is_use_trade_notifications(self):
        return self.pref_payload.use_trade_notifications
    
    def is_use_market_notifications(self):
        return self.pref_payload.use_market_notifications
    
    def is_use_price_notifications(self):
        return self.pref_payload.use_price_notifications
    
    def is_use_sound_for_mobile_notifications(self):
        return self.pref_payload.use_sound_for_mobile_notifications
    
    def is_tac_accepted_v120(self):
        return self.pref_payload.tac_accepted_v120
    
    def get_bsq_average_trim_threshold(self):
        return self.pref_payload.bsq_average_trim_threshold

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def update_trade_currencies(self, e: ObservableChangeEvent["FiatCurrency"]):
        if e.added_elements and len(e.added_elements) == 1 and self.initial_read_done:
            if e.added_elements[0] not in self.trade_currencies_as_observable:
                self.trade_currencies_as_observable.append(e.added_elements[0])
        if e.removed_elements and len(e.removed_elements) == 1 and self.initial_read_done:
            if e.removed_elements[0] in self.trade_currencies_as_observable:
                self.trade_currencies_as_observable.remove(e.removed_elements[0])
                
        self.request_persistence()
