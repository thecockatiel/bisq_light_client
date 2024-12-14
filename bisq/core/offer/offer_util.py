from typing import TYPE_CHECKING, Callable, Optional, Union
import uuid
from bisq.common.capabilities import Capabilities
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.common.util.utilities import get_random_prefix
import bisq.common.version as Version
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.locale.currency_util import get_currency_by_country_code, is_crypto_currency, is_fiat_currency
from bisq.core.locale.res import Res
from bisq.core.monetary.volume import Volume
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.payment.cash_by_mail_account import CashByMailAccount
from bisq.core.payment.f2f_account import F2FAccount
from bisq.core.provider.fee.fee_service import FeeService
from bisq.core.util.average_price_util import get_average_price_tuple
from bisq.core.util.coin.coin_util import CoinUtil
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from proto.pb_pb2 import OfferDirection
from bisq.core.monetary.price import Price

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.offer.bisq_v1.mutable_offer_payload_fields import MutableOfferPayloadFields
    from bisq.core.offer.open_offer import OpenOffer
    from bisq.core.payment.payload.payment_method import PaymentMethod
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.offer import Offer
    from bisq.core.util.coin.coin_formatter import CoinFormatter
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.account.witness.account_age_witness_service import AccountAgeWitnessService
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.trade.statistics.referral_id_service import ReferralIdService
    from bisq.core.trade.statistics.trade_statistics_manager import TradeStatisticsManager
    from bisq.core.user.preferences import Preferences

logger = get_logger(__name__)

# TODO: relies on transaction and trade statistics manager to be implemented
class OfferUtil:
    """This class holds utility methods for creating, editing and taking an Offer"""
    
    def __init__(self, 
                 account_age_witness_service: 'AccountAgeWitnessService',
                 bsq_wallet_service: 'BsqWalletService',
                 filter_manager: 'FilterManager',
                 preferences: 'Preferences',
                 price_feed_service: 'PriceFeedService',
                 p2p_service: 'P2PService',
                 referral_id_service: 'ReferralIdService',
                 trade_statistics_manager: 'TradeStatisticsManager'):
        self.account_age_witness_service = account_age_witness_service
        self.bsq_wallet_service = bsq_wallet_service
        self.filter_manager = filter_manager
        self.preferences = preferences
        self.price_feed_service = price_feed_service
        self.p2p_service = p2p_service
        self.referral_id_service = referral_id_service
        self.trade_statistics_manager = trade_statistics_manager
        
        self.is_valid_fee_payment_currency_code: Callable[[str], bool] = \
            lambda c: c.upper() in ["BSQ", "BTC"]
    
    @staticmethod
    def get_random_offer_id() -> str:
        return f"{get_random_prefix(5, 8)}-{uuid.uuid4()}-{OfferUtil.get_stripped_version()}"
    
    @staticmethod
    def get_stripped_version() -> str:
        return Version.VERSION.replace(".", "")
    
    # We add a counter at the end of the offer id signalling the number of times that offer has
    # been mutated ether due edit or due pow adjustments.
    @staticmethod
    def get_offer_id_with_mutation_counter(id: str) -> str:
        split = id.split("-")
        base = id
        counter = 0
        if len(split) > 7:
            counter_string = split[7]
            end_index = len(id) - len(counter_string) - 1
            base = id[:end_index]
            try:
                counter = int(counter_string)
            except (ValueError, TypeError):
                pass
        counter += 1
        return f"{base}-{counter}"
    
    @staticmethod
    def get_version_from_id(id: str) -> str:
        return id.split("-")[6]

    def maybe_set_fee_payment_currency_preference(self, fee_currency_code: str) -> None:
        if fee_currency_code:
            if not self.is_valid_fee_payment_currency_code(fee_currency_code):
                raise ValueError(f"{fee_currency_code.upper()} cannot be used to pay trade fees")

            if fee_currency_code.upper() == "BSQ" and self.preferences.is_pay_fee_in_btc():
                self.preferences.set_pay_fee_in_btc(False)
            elif fee_currency_code.upper() == "BTC" and not self.preferences.is_pay_fee_in_btc():
                self.preferences.set_pay_fee_in_btc(True)

    @staticmethod
    def is_buy_offer(direction: OfferDirection) -> bool:
        """
        Given the direction, is this a BUY?
        
        True for an offer to buy BTC from the taker, False for an offer to sell BTC to the taker.
        """
        return direction == OfferDirection.BUY

    def get_max_trade_limit(self, payment_account: 'PaymentAccount', 
                           currency_code: str,
                           direction: OfferDirection) -> int:
        return (self.account_age_witness_service.get_my_trade_limit(payment_account, currency_code, direction)
                if payment_account is not None else 0)

    @staticmethod
    def is_balance_sufficient(cost: Coin, balance: Coin) -> bool:
        """Return true if a balance can cover a cost."""
        return cost is not None and balance >= cost

    @staticmethod
    def get_balance_shortage(cost: Coin, balance: Coin) -> Coin:
        """Return the wallet balance shortage for a given trade cost, or zero if there is no shortage."""
        if cost is not None:
            shortage = cost.subtract(balance)
            return Coin.ZERO() if shortage.is_negative() else shortage
        return Coin.ZERO()
        
    def get_usable_bsq_balance(self) -> Coin:
        """
        Returns the usable BSQ balance.
        """
        # We have to keep a minimum amount of BSQ == bitcoin dust limit, otherwise there
        # would be dust violations for change UTXOs; essentially means the minimum usable
        # balance of BSQ is 5.46.
        usable_bsq_balance = self.bsq_wallet_service.get_available_balance().subtract(Restrictions.get_min_non_dust_output())
        return Coin.ZERO() if usable_bsq_balance.is_negative() else usable_bsq_balance

    @staticmethod
    def calculate_manual_price(volume_as_double: float, amount_as_double: float) -> float:
        return volume_as_double / amount_as_double

    @staticmethod
    def calculate_market_price_margin(manual_price: float, market_price: float) -> float:
        return MathUtils.round_double(manual_price / market_price, 4)

    def get_maker_fee(self, amount: Optional[Coin]) -> Optional[Coin]:
        """
        Returns the makerFee as Coin, this can be priced in BTC or BSQ.
        
        Args:
            amount: the amount of BTC to trade
        Returns:
            the maker fee for the given trade amount, or None if the amount is None
        """
        is_currency_for_maker_fee_btc = self.is_currency_for_maker_fee_btc(amount)
        return CoinUtil.get_maker_fee(is_currency_for_maker_fee_btc, amount)

    def get_tx_fee_by_vsize(self, tx_fee_per_vbyte_from_fee_service: Coin, vsize_in_vbytes: int) -> Coin:
        return tx_fee_per_vbyte_from_fee_service.multiply(self.get_average_taker_fee_tx_vsize(vsize_in_vbytes))

    @staticmethod
    def get_average_taker_fee_tx_vsize(tx_vsize: int) -> int:
        # We use the sum of the size of the trade fee and the deposit tx to get an average.
        # Miners will take the trade fee tx if the total fee of both dependent txs are good
        # enough. With that we avoid that we overpay in case that the trade fee has many
        # inputs and we would apply that fee for the other 2 txs as well. We still might
        # overpay a bit for the payout tx.
        return (tx_vsize + 233) // 2

    def is_currency_for_maker_fee_btc(self, amount: Optional[Coin]) -> bool:
        """
        Checks if the maker fee should be paid in BTC, this can be the case due to user
        preference or because the user doesn't have enough BSQ.

        Args:
            amount: the amount of BTC to trade
        Returns:
            True if BTC is preferred or the trade amount is nonnull and there isn't enough BSQ for it.
        """
        pay_fee_in_btc = self.preferences.is_pay_fee_in_btc()
        bsq_for_fee_available = self.is_bsq_for_maker_fee_available(amount)
        return pay_fee_in_btc or not bsq_for_fee_available

    def is_bsq_for_maker_fee_available(self, amount: Optional[Coin]) -> bool:
        """
        Checks if the available BSQ balance is sufficient to pay for the offer's maker fee.

        Args:
            amount: the amount of BTC to trade
        Returns:
            True if the balance is sufficient, False otherwise
        """
        available_balance = self.bsq_wallet_service.get_available_balance()
        maker_fee = CoinUtil.get_maker_fee(False, amount)

        # If we don't know yet the maker fee (amount is not set) we return true,
        # otherwise we would disable BSQ fee each time we open the create offer screen
        # as there the amount is not set.
        if maker_fee is None:
            return True

        surplus_funds = available_balance.subtract(maker_fee)
        if Restrictions.is_dust(surplus_funds):
            return False  # we can't be left with dust
        return not available_balance.subtract(maker_fee).is_negative()

    def get_taker_fee(self, is_currency_for_taker_fee_btc: bool, amount: Optional[Coin]) -> Optional[Coin]:
        if amount is not None:
            fee_per_btc = CoinUtil.get_fee_per_btc(FeeService.get_taker_fee_per_btc(is_currency_for_taker_fee_btc), amount)
            return CoinUtil.max_coin(fee_per_btc, FeeService.get_min_taker_fee(is_currency_for_taker_fee_btc))
        return None

    def is_currency_for_taker_fee_btc(self, amount: Coin) -> bool:
        pay_fee_in_btc = self.preferences.is_pay_fee_in_btc()
        bsq_for_fee_available = self.is_bsq_for_taker_fee_available(amount)
        return pay_fee_in_btc or not bsq_for_fee_available

    def is_bsq_for_taker_fee_available(self, amount: Optional[Coin]) -> bool:
        available_balance = self.bsq_wallet_service.get_available_balance()
        taker_fee = self.get_taker_fee(False, amount)

        # If we don't know yet the maker fee (amount is not set) we return true,
        # otherwise we would disable BSQ fee each time we open the create offer screen
        # as there the amount is not set.
        if taker_fee is None:
            return True

        surplus_funds = available_balance.subtract(taker_fee)
        if Restrictions.is_dust(surplus_funds):
            return False  # we can't be left with dust
        return not available_balance.subtract(taker_fee).is_negative()

    def is_blockchain_payment_method(self, offer: 'Offer') -> bool:
        return offer is not None and offer.payment_method.is_blockchain()

    def get_fee_in_user_fiat_currency(self, maker_fee: Coin,
                                    is_currency_for_maker_fee_btc: bool,
                                    bsq_formatter: 'CoinFormatter') -> Optional[Volume]:
        user_currency_code = self.preferences.get_preferred_trade_currency().code
        if is_crypto_currency(user_currency_code):
            # In case the user has selected a altcoin as preferred_trade_currency
            # we derive the fiat currency from the user country
            country_code = self.preferences.get_user_country().code
            user_currency_code = get_currency_by_country_code(country_code).code

        return self._get_fee_in_user_fiat_currency(maker_fee,
                                                is_currency_for_maker_fee_btc,
                                                user_currency_code,
                                                bsq_formatter)

    def _get_fee_in_user_fiat_currency(self, maker_fee: Coin,
                                     is_currency_for_maker_fee_btc: bool,
                                     user_currency_code: str,
                                     bsq_formatter: 'CoinFormatter') -> Optional[Volume]:
        market_price = self.price_feed_service.get_market_price(user_currency_code)
        if market_price is not None and maker_fee is not None:
            market_price_as_long = MathUtils.round_double_to_long(MathUtils.scale_up_by_power_of_10(market_price.price, Fiat.SMALLEST_UNIT_EXPONENT))
            user_currency_price = Price.value_of(user_currency_code, market_price_as_long)

            if is_currency_for_maker_fee_btc:
                return user_currency_price.get_volume_by_amount(maker_fee)
            else:
                # We use the current market price for the fiat currency and the 30 day average BSQ price
                tuple_result = get_average_price_tuple(self.preferences,
                                                                     self.trade_statistics_manager,
                                                                     30)
                bsq_price = tuple_result[1]
                if bsq_price.is_positive():
                    input_value = bsq_formatter.format_coin(maker_fee)
                    maker_fee_as_volume = Volume.parse(input_value, "BSQ")
                    required_btc = bsq_price.get_amount_by_volume(maker_fee_as_volume)
                    volume_by_amount = user_currency_price.get_volume_by_amount(required_btc)
                    return volume_by_amount
                else:
                    return None
        else:
            return None

    def get_extra_data_map(self, payment_account: 'PaymentAccount',
                          currency_code: str,
                          direction: OfferDirection) -> Optional[dict[str, str]]:
        extra_data_map: dict[str, str] = {}
        
        if is_fiat_currency(currency_code):
            my_witness_hash = self.account_age_witness_service.get_my_witness_hash_as_hex(
                payment_account.payment_account_payload)
            extra_data_map[OfferPayload.ACCOUNT_AGE_WITNESS_HASH] = my_witness_hash
        
        optional_referral_id = self.referral_id_service.get_optional_referral_id()
        if optional_referral_id:
            extra_data_map[OfferPayload.REFERRAL_ID] = optional_referral_id
            
        if isinstance(payment_account, F2FAccount):
            extra_data_map[OfferPayload.F2F_CITY] = payment_account.city
            extra_data_map[OfferPayload.F2F_EXTRA_INFO] = payment_account.extra_info
            
        if isinstance(payment_account, CashByMailAccount):
            extra_data_map[OfferPayload.CASH_BY_MAIL_EXTRA_INFO] = payment_account.extra_info
            
        extra_data_map[OfferPayload.CAPABILITIES] = Capabilities.app.to_string_list()
        
        if currency_code == "XMR" and direction == OfferDirection.SELL:
            auto_conf_settings = [
                e for e in self.preferences.get_auto_confirm_settings_list()
                if e.currency_code == "XMR" and e.enabled
            ]
            if auto_conf_settings:
                extra_data_map[OfferPayload.XMR_AUTO_CONF] = OfferPayload.XMR_AUTO_CONF_ENABLED_VALUE
                
        return extra_data_map if extra_data_map else None

    def validate_offer_data(self, buyer_security_deposit: float,
                          payment_account: 'PaymentAccount',
                          currency_code: str,
                          maker_fee: Coin) -> None:
        """
        Validates the offer data before creating an offer.
        
        Args:
            buyer_security_deposit: Security deposit percentage
            payment_account: Payment account to use
            currency_code: Currency code for the offer
            maker_fee: Maker fee as Coin
            
        Raises:
            ValueError: If any validation fails
        """
        self.validate_basic_offer_data(payment_account.payment_method, currency_code)
        assert maker_fee is not None, "maker_fee must not be None"
        
        max_deposit = Restrictions.get_max_buyer_security_deposit_as_percent()
        min_deposit = Restrictions.get_min_buyer_security_deposit_as_percent()
        
        if buyer_security_deposit > max_deposit:
            raise ValueError(f"securityDeposit must not exceed {max_deposit}")
        if buyer_security_deposit < min_deposit:
            raise ValueError(f"securityDeposit must not be less than {min_deposit}")

    def validate_basic_offer_data(self, payment_method: 'PaymentMethod', currency_code: str) -> None:
        """
        Validates basic offer data.
        
        Args:
            payment_method: Payment method to validate
            currency_code: Currency code to validate
            
        Raises:
            ValueError: If any validation fails
        """
        assert self.p2p_service.get_address() is not None, "Address must not be None"
        
        if self.filter_manager.is_currency_banned(currency_code):
            raise ValueError(Res.get("offerbook.warning.currencyBanned"))
        
        if self.filter_manager.is_payment_method_banned(payment_method):
            raise ValueError(Res.get("offerbook.warning.paymentMethodBanned"))

    def get_merged_offer_payload(self, open_offer: 'OpenOffer', 
                               mutable_offer_payload_fields: 'MutableOfferPayloadFields') -> 'OfferPayload':
        """
        Returns an edited payload: a merge of the original offerPayload and
        editedOfferPayload fields. Mutable fields are sourced from
        mutableOfferPayloadFields param, e.g., payment account details, price, etc.
        Immutable fields are sourced from the original openOffer param.
        """
        original = open_offer.offer.offer_payload
        if not original:
            raise ValueError("Original offer payload not found")
            
        return OfferPayload(
            id=original.id,
            date=original.date,
            owner_node_address=original.owner_node_address,
            pub_key_ring=original.pub_key_ring,
            direction=original.direction,
            price=mutable_offer_payload_fields.fixed_price,
            market_price_margin=mutable_offer_payload_fields.market_price_margin,
            use_market_based_price=mutable_offer_payload_fields.use_market_based_price,
            amount=original.amount,
            min_amount=original.min_amount,
            base_currency_code=mutable_offer_payload_fields.base_currency_code,
            counter_currency_code=mutable_offer_payload_fields.counter_currency_code,
            arbitrator_node_addresses=original.arbitrator_node_addresses,
            mediator_node_addresses=original.mediator_node_addresses,
            payment_method_id=mutable_offer_payload_fields.payment_method_id,
            maker_payment_account_id=mutable_offer_payload_fields.maker_payment_account_id,
            offer_fee_payment_tx_id=original.offer_fee_payment_tx_id,
            country_code=mutable_offer_payload_fields.country_code,
            accepted_country_codes=mutable_offer_payload_fields.accepted_country_codes,
            bank_id=mutable_offer_payload_fields.bank_id,
            accepted_bank_ids=mutable_offer_payload_fields.accepted_bank_ids,
            version_nr=original.version_nr,
            block_height_at_offer_creation=original.block_height_at_offer_creation,
            tx_fee=original.tx_fee,
            maker_fee=original.maker_fee,
            is_currency_for_maker_fee_btc=original.is_currency_for_maker_fee_btc,
            buyer_security_deposit=original.buyer_security_deposit,
            seller_security_deposit=original.seller_security_deposit,
            max_trade_limit=mutable_offer_payload_fields.max_trade_limit,
            max_trade_period=mutable_offer_payload_fields.max_trade_period,
            use_auto_close=original.use_auto_close,
            use_re_open_after_auto_close=original.use_re_open_after_auto_close,
            lower_close_price=original.lower_close_price,
            upper_close_price=original.upper_close_price,
            is_private_offer=original.is_private_offer,
            hash_of_challenge=original.hash_of_challenge,
            extra_data_map=mutable_offer_payload_fields.extra_data_map,
            protocol_version=original.protocol_version
        )

    @staticmethod
    def is_fiat_offer(offer: 'Offer') -> bool:
        return offer.base_currency_code == "BTC" and not offer.is_bsq_swap_offer

    @staticmethod
    def is_altcoin_offer(offer: 'Offer') -> bool:
        return offer.counter_currency_code == "BTC" and not offer.is_bsq_swap_offer

    @staticmethod
    def does_offer_amount_exceed_trade_limit(offer: 'Offer') -> bool:
        return offer.amount.is_greater_than(
            offer.payment_method.get_max_trade_limit_as_coin(offer.currency_code)
        )

    @staticmethod
    def get_invalid_maker_fee_tx_error_message(offer: 'Offer', 
                                              btc_wallet_service: 'BtcWalletService') -> Optional[str]:
        offer_fee_payment_tx_id = offer.offer_fee_payment_tx_id
        if not offer_fee_payment_tx_id:
            return None

        maker_fee_tx: Optional["Transaction"] = btc_wallet_service.get_transaction(offer_fee_payment_tx_id)
        if not maker_fee_tx:
            return None

        error_msg = None
        header = f"The offer with offer ID '{offer.short_id}' has an invalid maker fee transaction.\n\n"
        spending_transaction = None
        extra_string = ("\nYou have to remove that offer to avoid failed trades.\n"
                       "If this happened because of a bug please contact the Bisq developers "
                       "and you can request reimbursement for the lost maker fee.")

        if len(maker_fee_tx.outputs) > 1:
            # Our output to fund the deposit tx is at index 1
            output = maker_fee_tx.outputs[1]
            spent_by_transaction_input = output.spent_by
            if spent_by_transaction_input:
                spending_tx = (spent_by_transaction_input.connected_transaction 
                             if spent_by_transaction_input.connected_transaction else "null")
                spending_transaction = str(spending_tx) # TODO: check stringification later
                # This is an exceptional case so we do not translate the error msg
                error_msg = (
                    f"The output of the maker fee tx is already spent.\n{extra_string}\n\n"
                    f"Transaction input which spent the reserved funds for that offer: '"
                    f"{spent_by_transaction_input.connected_transaction.get_tx_id()}:" # TODO: check stringification later
                    f"{spent_by_transaction_input.connected_output.index if spent_by_transaction_input.connected_output else 'null'}'"
                )
                logger.error(f"spent_by_transaction_input {spent_by_transaction_input}")
        else:
            error_msg = (f"The maker fee tx is invalid as it does not has at least 2 outputs.{extra_string}\n"
                        f"MakerFeeTx={maker_fee_tx}")

        if not error_msg:
            return None

        error_msg = header + error_msg
        logger.error(error_msg)
        if spending_transaction:
            logger.error(f"Spending transaction: {spending_transaction}")

        return error_msg

