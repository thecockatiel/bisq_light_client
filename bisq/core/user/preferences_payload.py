from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.country import Country
from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
import proto.pb_pb2 as protobuf
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.user.preferences_const import CLEAR_DATA_AFTER_DAYS_INITIAL, INITIAL_TRADE_LIMIT

if TYPE_CHECKING:
    from bisq.core.user.block_chain_explorer import BlockChainExplorer
    from bisq.core.user.auto_confirm_settings import AutoConfirmSettings
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.locale.crypto_currency import CryptoCurrency
    from bisq.core.locale.fiat_currency import FiatCurrency
    from bisq.core.locale.trade_currency import TradeCurrency


class PreferencesPayload(PersistableEnvelope):
    
    def __init__(self, 
                 user_language: str = None,
                 user_country: "Country" = None,
                 fiat_currencies: list["FiatCurrency"] = None,
                 crypto_currencies: list["CryptoCurrency"] = None,
                 block_chain_explorer_main_net: "BlockChainExplorer" = None,
                 block_chain_explorer_test_net: "BlockChainExplorer" = None,
                 bsq_block_chain_explorer: "BlockChainExplorer" = None,
                 backup_directory: str = None,
                 auto_select_arbitrators: bool = True,
                 dont_show_again_map: dict[str, bool] = None,
                 tac_accepted: bool = False,
                 use_tor_for_bitcoin_j: bool = True,
                 show_own_offers_in_offer_book: bool = True,
                 preferred_trade_currency: "TradeCurrency" = None,
                 withdrawal_tx_fee_in_vbytes: int = 100,
                 use_custom_withdrawal_tx_fee: bool = False,
                 max_price_distance_in_percent: float = 0.3,
                 offer_book_chart_screen_currency_code: Optional[str] = None,
                 trade_charts_screen_currency_code: Optional[str] = None,
                 buy_screen_currency_code: Optional[str] = None,
                 sell_screen_currency_code: Optional[str] = None,
                 buy_screen_crypto_currency_code: Optional[str] = None,
                 sell_screen_crypto_currency_code: Optional[str] = None,
                 trade_statistics_tick_unit_index: int = 3,
                 resync_spv_requested: bool = False,
                 sort_market_currencies_numerically: bool = True,
                 use_percentage_based_price: bool = True,
                 peer_tag_map: dict[str, str] = None,
                 bitcoin_nodes: str = "",
                 ignore_traders_list: list[str] = None,
                 directory_chooser_path: str = None,
                 buyer_security_deposit_as_long: int = 0,
                 use_animations: bool = False,
                 css_theme: int = 0,
                 selected_payment_account_for_create_offer: "PaymentAccount" = None,
                 pay_fee_in_btc: bool = True,
                 bridge_addresses: list[str] = None,
                 bridge_option_ordinal: int = 0,
                 tor_transport_ordinal: int = 0,
                 custom_bridges: Optional[str] = None,
                 bitcoin_nodes_option_ordinal: int = 0,
                 referral_id: str = None,
                 phone_key_and_token: str = None,
                 use_sound_for_mobile_notifications: bool = True,
                 use_trade_notifications: bool = True,
                 use_market_notifications: bool = True,
                 use_price_notifications: bool = True,
                 use_standby_mode: bool = False,
                 is_dao_full_node: bool = False,
                 rpc_user: str = None,
                 rpc_pw: str = None,
                 take_offer_selected_payment_account_id: str = None,
                 buyer_security_deposit_as_percent: float = None,
                 ignore_dust_threshold: int = 600,
                 clear_data_after_days: int = CLEAR_DATA_AFTER_DAYS_INITIAL,
                 buyer_security_deposit_as_percent_for_crypto: float = None,
                 block_notify_port: int = 0,
                 tac_accepted_v120: bool = False,
                 bsq_average_trim_threshold: float = 0.05,
                 auto_confirm_settings_list: list["AutoConfirmSettings"] = None,
                 hide_non_account_payment_methods: bool = False,
                 show_offers_matching_my_accounts: bool = False,
                 deny_api_taker: bool = False,
                 notify_on_pre_release: bool = False,
                 use_full_mode_dao_monitor: bool = False,
                 use_bitcoin_uris_in_qr_codes: bool = True,
                 user_defined_trade_limit: int = INITIAL_TRADE_LIMIT,
                 user_has_raised_trade_limit: bool = False,
                 process_burning_man_accounting_data: bool = False,
                 is_full_bm_accounting_node: bool = False,
                 use_bisq_wallet_funding: bool = False):
        self.user_language = user_language
        self.user_country = user_country
        self.fiat_currencies = fiat_currencies or []
        self.crypto_currencies = crypto_currencies or []
        self.block_chain_explorer_main_net = block_chain_explorer_main_net
        self.block_chain_explorer_test_net = block_chain_explorer_test_net
        self.bsq_block_chain_explorer = bsq_block_chain_explorer
        self.backup_directory = backup_directory
        self.auto_select_arbitrators = auto_select_arbitrators
        self.dont_show_again_map = dont_show_again_map or {}
        self.tac_accepted = tac_accepted
        self.use_tor_for_bitcoin_j = use_tor_for_bitcoin_j
        self.show_own_offers_in_offer_book = show_own_offers_in_offer_book
        self.preferred_trade_currency = preferred_trade_currency
        self.withdrawal_tx_fee_in_vbytes = withdrawal_tx_fee_in_vbytes
        self.use_custom_withdrawal_tx_fee = use_custom_withdrawal_tx_fee
        self.max_price_distance_in_percent = max_price_distance_in_percent
        self.offer_book_chart_screen_currency_code = offer_book_chart_screen_currency_code
        self.trade_charts_screen_currency_code = trade_charts_screen_currency_code
        self.buy_screen_currency_code = buy_screen_currency_code
        self.sell_screen_currency_code = sell_screen_currency_code
        self.buy_screen_crypto_currency_code = buy_screen_crypto_currency_code
        self.sell_screen_crypto_currency_code = sell_screen_crypto_currency_code
        self.trade_statistics_tick_unit_index = trade_statistics_tick_unit_index
        self.resync_spv_requested = resync_spv_requested
        self.sort_market_currencies_numerically = sort_market_currencies_numerically
        self.use_percentage_based_price = use_percentage_based_price
        self.peer_tag_map = peer_tag_map or {}
        # custom btc nodes
        self.bitcoin_nodes = bitcoin_nodes
        self.ignore_traders_list = ignore_traders_list or []
        self.directory_chooser_path = directory_chooser_path
        """don't use this in python implementation"""
        
        # Superseded by buyerSecurityDepositAsPercent
        self.buyer_security_deposit_as_long = buyer_security_deposit_as_long # Deprecated
        
        self.use_animations = use_animations
        self.css_theme = css_theme
        self.selected_payment_account_for_create_offer = selected_payment_account_for_create_offer
        self.pay_fee_in_btc = pay_fee_in_btc
        self.bridge_addresses = bridge_addresses or []
        self.bridge_option_ordinal = bridge_option_ordinal
        self.tor_transport_ordinal = tor_transport_ordinal
        self.custom_bridges = custom_bridges
        self.bitcoin_nodes_option_ordinal = bitcoin_nodes_option_ordinal
        self.referral_id = referral_id
        self.phone_key_and_token = phone_key_and_token
        self.use_sound_for_mobile_notifications = use_sound_for_mobile_notifications
        self.use_trade_notifications = use_trade_notifications
        self.use_market_notifications = use_market_notifications
        self.use_price_notifications = use_price_notifications
        self.use_standby_mode = use_standby_mode
        self.is_dao_full_node = is_dao_full_node
        self.rpc_user = rpc_user
        self.rpc_pw = rpc_pw
        self.take_offer_selected_payment_account_id = take_offer_selected_payment_account_id
        self.buyer_security_deposit_as_percent = buyer_security_deposit_as_percent or Restrictions.get_default_buyer_security_deposit_as_percent()
        self.ignore_dust_threshold = ignore_dust_threshold
        self.clear_data_after_days = clear_data_after_days
        self.buyer_security_deposit_as_percent_for_crypto = buyer_security_deposit_as_percent_for_crypto or Restrictions.get_default_buyer_security_deposit_as_percent()
        self.block_notify_port = block_notify_port
        self.tac_accepted_v120 = tac_accepted_v120
        self.bsq_average_trim_threshold = bsq_average_trim_threshold
        
        # Added at 1.3.8
        self.auto_confirm_settings_list = auto_confirm_settings_list or []
        
        # Added in 1.5.5
        self.hide_non_account_payment_methods = hide_non_account_payment_methods
        self.show_offers_matching_my_accounts = show_offers_matching_my_accounts
        self.deny_api_taker = deny_api_taker
        self.notify_on_pre_release = notify_on_pre_release
        self.use_full_mode_dao_monitor = use_full_mode_dao_monitor
        self.use_bitcoin_uris_in_qr_codes = use_bitcoin_uris_in_qr_codes
        
        
        self.user_defined_trade_limit = user_defined_trade_limit
        self.user_has_raised_trade_limit = user_has_raised_trade_limit
        
        # Added at 1.9.11
        self.process_burning_man_accounting_data = process_burning_man_accounting_data
        
        # Added at 1.9.11
        self.is_full_bm_accounting_node = is_full_bm_accounting_node
        
        self.use_bisq_wallet_funding = use_bisq_wallet_funding

    def to_proto_message(self):
        builder = protobuf.PreferencesPayload(
            user_language=self.user_language,
            user_country=self.user_country.to_proto_message() if self.user_country else None,
            fiat_currencies=[currency.to_proto_message() for currency in self.fiat_currencies],
            crypto_currencies=[currency.to_proto_message() for currency in self.crypto_currencies],
            block_chain_explorer_main_net=self.block_chain_explorer_main_net.to_proto_message(),
            block_chain_explorer_test_net=self.block_chain_explorer_test_net.to_proto_message(),
            auto_select_arbitrators=self.auto_select_arbitrators,
            dont_show_again_map=self.dont_show_again_map,
            tac_accepted=self.tac_accepted,
            use_tor_for_bitcoin_j=self.use_tor_for_bitcoin_j,
            show_own_offers_in_offer_book=self.show_own_offers_in_offer_book,
            withdrawal_tx_fee_in_vbytes=self.withdrawal_tx_fee_in_vbytes,
            use_custom_withdrawal_tx_fee=self.use_custom_withdrawal_tx_fee,
            max_price_distance_in_percent=self.max_price_distance_in_percent,
            trade_statistics_tick_unit_index=self.trade_statistics_tick_unit_index,
            resync_Spv_requested=self.resync_spv_requested, # weird protobuf names
            sort_market_currencies_numerically=self.sort_market_currencies_numerically,
            use_percentage_based_price=self.use_percentage_based_price,
            peer_tag_map=self.peer_tag_map,
            bitcoin_nodes=self.bitcoin_nodes,
            ignore_traders_list=self.ignore_traders_list,
            directory_chooser_path=self.directory_chooser_path,
            buyer_security_deposit_as_long=self.buyer_security_deposit_as_long,
            use_animations=self.use_animations,
            css_theme=self.css_theme,
            pay_fee_in_Btc=self.pay_fee_in_btc, # weird protobuf names
            bridge_option_ordinal=self.bridge_option_ordinal,
            tor_transport_ordinal=self.tor_transport_ordinal,
            bitcoin_nodes_option_ordinal=self.bitcoin_nodes_option_ordinal,
            use_sound_for_mobile_notifications=self.use_sound_for_mobile_notifications,
            use_trade_notifications=self.use_trade_notifications,
            use_market_notifications=self.use_market_notifications,
            use_price_notifications=self.use_price_notifications,
            use_standby_mode=self.use_standby_mode,
            is_dao_full_node=self.is_dao_full_node,
            buyer_security_deposit_as_percent=self.buyer_security_deposit_as_percent,
            ignore_dust_threshold=self.ignore_dust_threshold,
            clear_data_after_days=self.clear_data_after_days,
            buyer_security_deposit_as_percent_for_crypto=self.buyer_security_deposit_as_percent_for_crypto,
            block_notify_port=self.block_notify_port,
            tac_accepted_v120=self.tac_accepted_v120,
            bsq_average_trim_threshold=self.bsq_average_trim_threshold,
            auto_confirm_settings=[setting.to_proto_message() for setting in self.auto_confirm_settings_list],
            hide_non_account_payment_methods=self.hide_non_account_payment_methods,
            show_offers_matching_my_accounts=self.show_offers_matching_my_accounts,
            deny_api_taker=self.deny_api_taker,
            notify_on_pre_release=self.notify_on_pre_release,
            use_full_mode_dao_monitor=self.use_full_mode_dao_monitor,
            use_bitcoin_uris_in_qr_codes=self.use_bitcoin_uris_in_qr_codes,
            user_defined_trade_limit=self.user_defined_trade_limit,
            user_has_raised_trade_limit=self.user_has_raised_trade_limit,
            process_burning_man_accounting_data=self.process_burning_man_accounting_data,
            is_full_b_m_accounting_node=self.is_full_bm_accounting_node, # weird protobuf names
            use_bisq_wallet_funding=self.use_bisq_wallet_funding
        )

        if self.backup_directory:
            builder.backup_directory = self.backup_directory
        if self.preferred_trade_currency:
            builder.preferred_trade_currency.CopyFrom(self.preferred_trade_currency.to_proto_message())
        if self.offer_book_chart_screen_currency_code:
            builder.offer_book_chart_screen_currency_code = self.offer_book_chart_screen_currency_code
        if self.trade_charts_screen_currency_code:
            builder.trade_charts_screen_currency_code = self.trade_charts_screen_currency_code
        if self.buy_screen_currency_code:
            builder.buy_screen_currency_code = self.buy_screen_currency_code
        if self.sell_screen_currency_code:
            builder.sell_screen_currency_code = self.sell_screen_currency_code
        if self.buy_screen_crypto_currency_code:
            builder.buy_screen_crypto_currency_code = self.buy_screen_crypto_currency_code
        if self.sell_screen_crypto_currency_code:
            builder.sell_screen_crypto_currency_code = self.sell_screen_crypto_currency_code
        if self.selected_payment_account_for_create_offer:
            # weird protobuf names
            builder.selectedPayment_account_for_createOffer.CopyFrom(self.selected_payment_account_for_create_offer.to_proto_message())
        if self.bridge_addresses:
            builder.bridge_addresses.extend(self.bridge_addresses)
        if self.custom_bridges:
            builder.custom_bridges = self.custom_bridges
        if self.referral_id:
            builder.referral_id = self.referral_id
        if self.phone_key_and_token:
            builder.phone_key_and_token = self.phone_key_and_token
        if self.rpc_user:
            builder.rpc_user = self.rpc_user
        if self.rpc_pw:
            builder.rpc_pw = self.rpc_pw
        if self.take_offer_selected_payment_account_id:
            builder.take_offer_selected_payment_account_id = self.take_offer_selected_payment_account_id
        if self.bsq_block_chain_explorer:
            builder.bsq_block_chain_explorer.CopyFrom(self.bsq_block_chain_explorer.to_proto_message())

        return protobuf.PersistableEnvelope(preferences_payload=builder)
    
    @staticmethod
    def from_proto(proto: protobuf.PreferencesPayload, core_proto_resolver: "CoreProtoResolver"):
        payment_account = None
        # weird protobuf names
        if (proto.HasField('selectedPayment_account_for_createOffer') and 
            proto.selectedPayment_account_for_createOffer.HasField('payment_method')):  
            payment_account = PaymentAccount.from_proto(proto.selectedPayment_account_for_createOffer, core_proto_resolver)
        
        return PreferencesPayload(
            user_language=proto.user_language,
            user_country=Country.from_proto(proto.user_country) if proto.user_country else None,
            fiat_currencies=[FiatCurrency.from_proto(c) for c in proto.fiat_currencies] if proto.fiat_currencies else [],
            crypto_currencies=[CryptoCurrency.from_proto(c) for c in proto.crypto_currencies] if proto.crypto_currencies else [],
            block_chain_explorer_main_net=BlockChainExplorer.from_proto(proto.block_chain_explorer_main_net),
            block_chain_explorer_test_net=BlockChainExplorer.from_proto(proto.block_chain_explorer_test_net),
            bsq_block_chain_explorer=BlockChainExplorer.from_proto(proto.bsq_block_chain_explorer) if proto.HasField('bsq_block_chain_explorer') else None,
            backup_directory=ProtoUtil.string_or_none_from_proto(proto.backup_directory),
            auto_select_arbitrators=proto.auto_select_arbitrators,
            dont_show_again_map=dict(proto.dont_show_again_map),
            tac_accepted=proto.tac_accepted,
            use_tor_for_bitcoin_j=proto.use_tor_for_bitcoin_j,
            show_own_offers_in_offer_book=proto.show_own_offers_in_offer_book,
            preferred_trade_currency=TradeCurrency.from_proto(proto.preferred_trade_currency) if proto.HasField('preferred_trade_currency') else None,
            withdrawal_tx_fee_in_vbytes=proto.withdrawal_tx_fee_in_vbytes,
            use_custom_withdrawal_tx_fee=proto.use_custom_withdrawal_tx_fee,
            max_price_distance_in_percent=proto.max_price_distance_in_percent,
            offer_book_chart_screen_currency_code=ProtoUtil.string_or_none_from_proto(proto.offer_book_chart_screen_currency_code),
            trade_charts_screen_currency_code=ProtoUtil.string_or_none_from_proto(proto.trade_charts_screen_currency_code),
            buy_screen_currency_code=ProtoUtil.string_or_none_from_proto(proto.buy_screen_currency_code),
            sell_screen_currency_code=ProtoUtil.string_or_none_from_proto(proto.sell_screen_currency_code),
            buy_screen_crypto_currency_code=ProtoUtil.string_or_none_from_proto(proto.buy_screen_crypto_currency_code),
            sell_screen_crypto_currency_code=ProtoUtil.string_or_none_from_proto(proto.sell_screen_crypto_currency_code),
            trade_statistics_tick_unit_index=proto.trade_statistics_tick_unit_index,
            resync_spv_requested=proto.resync_Spv_requested, # weird protobuf names
            sort_market_currencies_numerically=proto.sort_market_currencies_numerically,
            use_percentage_based_price=proto.use_percentage_based_price,
            peer_tag_map=dict(proto.peer_tag_map),
            bitcoin_nodes=proto.bitcoin_nodes,
            ignore_traders_list=list(proto.ignore_traders_list),
            directory_chooser_path=proto.directory_chooser_path,
            buyer_security_deposit_as_long=proto.buyer_security_deposit_as_long,
            use_animations=proto.use_animations,
            css_theme=proto.css_theme,
            selected_payment_account_for_create_offer=payment_account,
            pay_fee_in_btc=proto.pay_fee_in_Btc, # weird protobuf names
            bridge_addresses=list(proto.bridge_addresses) if proto.bridge_addresses else None,
            bridge_option_ordinal=proto.bridge_option_ordinal,
            tor_transport_ordinal=proto.tor_transport_ordinal,
            custom_bridges=ProtoUtil.string_or_none_from_proto(proto.custom_bridges),
            bitcoin_nodes_option_ordinal=proto.bitcoin_nodes_option_ordinal,
            referral_id=proto.referral_id if proto.referral_id else None,
            phone_key_and_token=proto.phone_key_and_token if proto.phone_key_and_token else None,
            use_sound_for_mobile_notifications=proto.use_sound_for_mobile_notifications,
            use_trade_notifications=proto.use_trade_notifications,
            use_market_notifications=proto.use_market_notifications,
            use_price_notifications=proto.use_price_notifications,
            use_standby_mode=proto.use_standby_mode,
            is_dao_full_node=proto.is_dao_full_node,
            rpc_user=proto.rpc_user if proto.rpc_user else None,
            rpc_pw=proto.rpc_pw if proto.rpc_pw else None,
            take_offer_selected_payment_account_id=proto.take_offer_selected_payment_account_id if proto.take_offer_selected_payment_account_id else None,
            buyer_security_deposit_as_percent=proto.buyer_security_deposit_as_percent,
            ignore_dust_threshold=proto.ignore_dust_threshold,
            clear_data_after_days=proto.clear_data_after_days,
            buyer_security_deposit_as_percent_for_crypto=proto.buyer_security_deposit_as_percent_for_crypto,
            block_notify_port=proto.block_notify_port,
            tac_accepted_v120=proto.tac_accepted_v120,
            bsq_average_trim_threshold=proto.bsq_average_trim_threshold,
            auto_confirm_settings_list=[AutoConfirmSettings.from_proto(s) for s in proto.auto_confirm_settings] if proto.auto_confirm_settings else [],
            hide_non_account_payment_methods=proto.hide_non_account_payment_methods,
            show_offers_matching_my_accounts=proto.show_offers_matching_my_accounts,
            deny_api_taker=proto.deny_api_taker,
            notify_on_pre_release=proto.notify_on_pre_release,
            use_full_mode_dao_monitor=proto.use_full_mode_dao_monitor,
            use_bitcoin_uris_in_qr_codes=proto.use_bitcoin_uris_in_qr_codes,
            user_defined_trade_limit=proto.user_defined_trade_limit if proto.user_has_raised_trade_limit else INITIAL_TRADE_LIMIT,
            user_has_raised_trade_limit=proto.user_has_raised_trade_limit,
            process_burning_man_accounting_data=proto.process_burning_man_accounting_data,
            is_full_bm_accounting_node=proto.is_full_b_m_accounting_node,  # weird protobuf names
            use_bisq_wallet_funding=proto.use_bisq_wallet_funding
        )
