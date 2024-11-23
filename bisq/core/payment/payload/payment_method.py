import re
from datetime import timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.locale.currency_util import get_mature_market_currencies
from bisq.core.payment.trade_limits import TradeLimits
import proto.pb_pb2 as protobuf
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.locale.trade_currency import TradeCurrency

logger = get_logger(__name__)

class PaymentMethod(PersistablePayload):
    # For sorting payment methods, we want names that contain only ASCII and Extended-ASCII to go *below* other languages
    ASCII_PATTERN = re.compile(r'[\x00-\xFF]*')
    
    # time in blocks (average 10 min for one block confirmation
    DAY_MS = int(timedelta(hours=24).total_seconds() * 1000)

    # Default trade limits.
    # We initialize very early before reading persisted data. We will apply later the limit from
    # the DAO param (Param.MAX_TRADE_LIMIT) but that can be only done after the dao is initialized.
    # The default values will be used for deriving the
    # risk factor so the relation between the risk categories stays the same as with the default values.
    # We must not change those values as it could lead to invalid offers if amount becomes lower then new trade limit.
    # Increasing might be ok, but needs more thought as well...
    DEFAULT_TRADE_LIMIT_VERY_LOW_RISK = Coin.parse_coin("1")
    DEFAULT_TRADE_LIMIT_LOW_RISK = Coin.parse_coin("0.5")
    DEFAULT_TRADE_LIMIT_MID_RISK = Coin.parse_coin("0.25")
    DEFAULT_TRADE_LIMIT_HIGH_RISK = Coin.parse_coin("0.125")

    # Payment method IDs
    UPHOLD_ID = "UPHOLD"
    MONEY_BEAM_ID = "MONEY_BEAM"
    POPMONEY_ID = "POPMONEY"
    REVOLUT_ID = "REVOLUT"
    PERFECT_MONEY_ID = "PERFECT_MONEY"
    SEPA_ID = "SEPA"
    SEPA_INSTANT_ID = "SEPA_INSTANT"
    FASTER_PAYMENTS_ID = "FASTER_PAYMENTS"
    NATIONAL_BANK_ID = "NATIONAL_BANK"
    JAPAN_BANK_ID = "JAPAN_BANK"
    AUSTRALIA_PAYID_ID = "AUSTRALIA_PAYID"
    SAME_BANK_ID = "SAME_BANK"
    SPECIFIC_BANKS_ID = "SPECIFIC_BANKS"
    SWISH_ID = "SWISH"
    ALI_PAY_ID = "ALI_PAY"
    WECHAT_PAY_ID = "WECHAT_PAY"
    CLEAR_X_CHANGE_ID = "CLEAR_X_CHANGE"

    CHASE_QUICK_PAY_ID = "CHASE_QUICK_PAY" # Removed due to QuickPay becoming Zelle

    INTERAC_E_TRANSFER_ID = "INTERAC_E_TRANSFER"
    US_POSTAL_MONEY_ORDER_ID = "US_POSTAL_MONEY_ORDER"
    CASH_DEPOSIT_ID = "CASH_DEPOSIT"
    MONEY_GRAM_ID = "MONEY_GRAM"
    WESTERN_UNION_ID = "WESTERN_UNION"
    HAL_CASH_ID = "HAL_CASH"
    F2F_ID = "F2F"
    BLOCK_CHAINS_ID = "BLOCK_CHAINS"
    PROMPT_PAY_ID = "PROMPT_PAY"
    ADVANCED_CASH_ID = "ADVANCED_CASH"
    TRANSFERWISE_ID = "TRANSFERWISE"
    TRANSFERWISE_USD_ID = "TRANSFERWISE_USD"
    PAYSERA_ID = "PAYSERA"
    PAXUM_ID = "PAXUM"
    NEFT_ID = "NEFT"
    RTGS_ID = "RTGS"
    IMPS_ID = "IMPS"
    UPI_ID = "UPI"
    PAYTM_ID = "PAYTM"
    NEQUI_ID = "NEQUI"
    BIZUM_ID = "BIZUM"
    PIX_ID = "PIX"
    AMAZON_GIFT_CARD_ID = "AMAZON_GIFT_CARD"
    BLOCK_CHAINS_INSTANT_ID = "BLOCK_CHAINS_INSTANT"
    CASH_BY_MAIL_ID = "CASH_BY_MAIL"
    CAPITUAL_ID = "CAPITUAL"
    CELPAY_ID = "CELPAY"
    MONESE_ID = "MONESE"
    SATISPAY_ID = "SATISPAY"
    TIKKIE_ID = "TIKKIE"
    VERSE_ID = "VERSE"
    STRIKE_ID = "STRIKE"
    SWIFT_ID = "SWIFT"
    ACH_TRANSFER_ID = "ACH_TRANSFER"
    DOMESTIC_WIRE_TRANSFER_ID = "DOMESTIC_WIRE_TRANSFER"
    BSQ_SWAP_ID = "BSQ_SWAP"
    MERCADO_PAGO_ID = "MERCADO_PAGO"
    SBP_ID = "SBP"

    # Cannot be deleted as it would break old trade history entries
    OK_PAY_ID = "OK_PAY"  # Deprecated
    CASH_APP_ID = "CASH_APP"  # Deprecated, Removed due too high chargeback risk
    VENMO_ID = "VENMO"  # Deprecated,  Removed due too high chargeback risk
    

    UPHOLD: "PaymentMethod" = None
    MONEY_BEAM: "PaymentMethod" = None
    POPMONEY: "PaymentMethod" = None
    REVOLUT: "PaymentMethod" = None
    PERFECT_MONEY: "PaymentMethod" = None
    SEPA: "PaymentMethod" = None
    SEPA_INSTANT: "PaymentMethod" = None
    FASTER_PAYMENTS: "PaymentMethod" = None
    NATIONAL_BANK: "PaymentMethod" = None
    JAPAN_BANK: "PaymentMethod" = None
    AUSTRALIA_PAYID: "PaymentMethod" = None
    SAME_BANK: "PaymentMethod" = None
    SPECIFIC_BANKS: "PaymentMethod" = None
    SWISH: "PaymentMethod" = None
    ALI_PAY: "PaymentMethod" = None
    WECHAT_PAY: "PaymentMethod" = None
    CLEAR_X_CHANGE: "PaymentMethod" = None
    CHASE_QUICK_PAY: "PaymentMethod" = None
    INTERAC_E_TRANSFER: "PaymentMethod" = None
    US_POSTAL_MONEY_ORDER: "PaymentMethod" = None
    CASH_DEPOSIT: "PaymentMethod" = None
    MONEY_GRAM: "PaymentMethod" = None
    WESTERN_UNION: "PaymentMethod" = None
    F2F: "PaymentMethod" = None
    HAL_CASH: "PaymentMethod" = None
    BLOCK_CHAINS: "PaymentMethod" = None
    PROMPT_PAY: "PaymentMethod" = None
    ADVANCED_CASH: "PaymentMethod" = None
    TRANSFERWISE: "PaymentMethod" = None
    TRANSFERWISE_USD: "PaymentMethod" = None
    PAYSERA: "PaymentMethod" = None
    PAXUM: "PaymentMethod" = None
    NEFT: "PaymentMethod" = None
    RTGS: "PaymentMethod" = None
    IMPS: "PaymentMethod" = None
    UPI: "PaymentMethod" = None
    PAYTM: "PaymentMethod" = None
    NEQUI: "PaymentMethod" = None
    BIZUM: "PaymentMethod" = None
    PIX: "PaymentMethod" = None
    AMAZON_GIFT_CARD: "PaymentMethod" = None
    BLOCK_CHAINS_INSTANT: "PaymentMethod" = None
    CASH_BY_MAIL: "PaymentMethod" = None
    CAPITUAL: "PaymentMethod" = None
    CELPAY: "PaymentMethod" = None
    MONESE: "PaymentMethod" = None
    SATISPAY: "PaymentMethod" = None
    TIKKIE: "PaymentMethod" = None
    VERSE: "PaymentMethod" = None
    STRIKE: "PaymentMethod" = None
    SWIFT: "PaymentMethod" = None
    ACH_TRANSFER: "PaymentMethod" = None
    DOMESTIC_WIRE_TRANSFER: "PaymentMethod" = None
    BSQ_SWAP: "PaymentMethod" = None
    MERCADO_PAGO: "PaymentMethod" = None
    SBP: "PaymentMethod" = None
    
    # Cannot be deleted as it would break old trade history entries (initialized after class definition)
    OK_PAY: "PaymentMethod" = None
    CASH_APP: "PaymentMethod" = None # Removed due too high chargeback risk
    VENMO: "PaymentMethod" = None # Removed due too high chargeback risk
    
    # The limit and duration assignment must not be changed as that could break old offers (if amount would be higher
    # than new trade limit) and violate the maker expectation when he created the offer (duration).
    PAYMENT_METHODS: tuple["PaymentMethod"] = tuple() # initialized after class definition
    
    PAYMENT_METHOD_MAP: dict[str, "PaymentMethod"] = dict() # initialized after class definition
    
    @staticmethod
    def get_payment_methods():
        return PaymentMethod.PAYMENT_METHODS
    
    @staticmethod
    def get_dummy_payment_method(id: str):
        return PaymentMethod(id, 0, Coin.ZERO())
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Instance fields
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    id: str
    
    # Must not change as old offers would get a new period then and that would violate the makers "contract" or
    # expectation when he created the offer.
    max_trade_period: int
    
    # With v0.9.4 we changed context of that field. Before it was the hard coded trade limit. Now it is the default
    # limit which will be used just in time to adjust the real trade limit based on the DAO param value and risk factor.
    # The risk factor is derived from the maxTradeLimit.
    # As that field is used in protobuffer definitions we cannot change it to reflect better the new context. We prefer
    # to keep the convention that PB fields has the same name as the Java class field (as we could rename it in
    # Java without breaking PB).
    max_trade_limit: int
    
    
    def __init__(self, id: str, max_trade_period: int = 0, max_trade_limit: Coin = Coin.ZERO()) -> None:
        super().__init__()
        self.id = id
        # default 0 values are Used for dummy entries in payment methods list (SHOW_ALL)
        self.max_trade_period = max_trade_period
        self.max_trade_limit = max_trade_limit.value
        
    def __str__(self) -> str:
        return f"PaymentMethod(id={self.id}, max_trade_period={self.max_trade_period}, max_trade_limit={self.max_trade_limit})"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PaymentMethod):
            return False
        return self.id == value.id
    
    def __hash__(self) -> int:
        return hash(self.id)

    def to_proto_message(self):
        raise protobuf.PaymentMethod(
            id=self.id,
            max_trade_period=self.max_trade_period,
            max_trade_limit=self.max_trade_limit,
        )
        
    @staticmethod
    def from_proto(proto: protobuf.PaymentMethod):
        return PaymentMethod(
            id=proto.id,
            max_trade_period=proto.max_trade_period,
            max_trade_limit=Coin.value_of(proto.max_trade_limit),
        )
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @staticmethod
    def get_payment_method(id: str):
        method = PaymentMethod.get_active_payment_method(id)
        if method is None:
            return PaymentMethod("shared.na") # TODO: res implementation
        return method 
    
    # We look up only our active payment methods not retired ones.
    @staticmethod
    def get_active_payment_method(id: str) -> Optional["PaymentMethod"]:
        return PaymentMethod.PAYMENT_METHOD_MAP.get(id)

    # We leave currencyCode as param for being flexible if we need custom handling of a currency in future
    # again (as we had in the past)
    def get_max_trade_limit_as_coin(self, currency_code: str) -> Coin:
        # We adjust the custom trade limits with the factor of the change of the DAO param. Initially it was set to 2 BTC.
        initial_trade_limit = 200000000
        trade_limits = TradeLimits.INSTANCE
        if trade_limits is None:
            # is null in some tests...
            logger.warning("trade_limits was null")
            return Coin.value_of(initial_trade_limit)
        
        max_trade_limit_from_dao_param = trade_limits.get_max_trade_limit_from_dao_param().value

        # Payment methods which define their own trade limits
        if self.id in [PaymentMethod.NEFT_ID, PaymentMethod.UPI_ID, PaymentMethod.PAYTM_ID, PaymentMethod.BIZUM_ID, PaymentMethod.TIKKIE_ID]:
            factor = max_trade_limit_from_dao_param / initial_trade_limit
            value = round(Coin.value_of(self.max_trade_limit).value * factor)
            return Coin.value_of(value)

        # We use the class field max_trade_limit only for mapping the risk factor.
        if self.max_trade_limit == PaymentMethod.DEFAULT_TRADE_LIMIT_VERY_LOW_RISK.value:
            risk_factor = 1
        elif self.max_trade_limit == PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK.value:
            risk_factor = 2
        elif self.max_trade_limit == PaymentMethod.DEFAULT_TRADE_LIMIT_MID_RISK.value:
            risk_factor = 4
        elif self.max_trade_limit == PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK.value:
            risk_factor = 8
        else:
            risk_factor = 8
            logger.warning(
                "max_trade_limit is not matching one of our default values. We use highest risk factor. "
                f"max_trade_limit={Coin.value_of(self.max_trade_limit).to_friendly_string()}. PaymentMethod={self}"
            )

        return Coin.value_of(
            trade_limits.get_rounded_risk_based_trade_limit(max_trade_limit_from_dao_param, risk_factor)
        )
        
    def get_short_name(self) -> str:
        # in cases where translation is not found, Res.get() simply returns the key string
        # so no need for special error-handling code.
        return self.id + "_SHORT" # TODO: Res

    def get_display_string(self) -> str:
        return self.id # TODO: Res
 
    def is_fiat(self) -> bool:
        return not self.is_altcoin()

    def is_blockchain(self) -> bool:
        return self == PaymentMethod.BLOCK_CHAINS_INSTANT or self == PaymentMethod.BLOCK_CHAINS

    def is_altcoin(self) -> bool:
        return self.is_blockchain() or self.is_bsq_swap()

    def is_bsq_swap(self) -> bool:
        return self == PaymentMethod.BSQ_SWAP

    @staticmethod
    def has_chargeback_risk(payment_method: "PaymentMethod", trade_currencies: list["TradeCurrency"]) -> bool:
        return any(PaymentMethod.has_chargeback_risk(payment_method, trade_currency.code) for trade_currency in trade_currencies)

    @staticmethod
    def has_chargeback_risk(payment_method: "PaymentMethod") -> bool:
        return PaymentMethod.has_chargeback_risk(payment_method, get_mature_market_currencies())

    @staticmethod
    def has_chargeback_risk(payment_method: "PaymentMethod", currency_code: str) -> bool:
        if payment_method is None:
            return False

        id = payment_method.id
        return PaymentMethod.has_chargeback_risk(id, currency_code)

    @staticmethod
    def has_chargeback_risk(id: str, currency_code: str) -> bool:
        if not any(c.code == currency_code for c in get_mature_market_currencies()):
            return False

        return id in [
            PaymentMethod.SEPA_ID,
            PaymentMethod.SEPA_INSTANT_ID,
            PaymentMethod.INTERAC_E_TRANSFER_ID,
            PaymentMethod.CLEAR_X_CHANGE_ID,
            PaymentMethod.REVOLUT_ID,
            PaymentMethod.NATIONAL_BANK_ID,
            PaymentMethod.SAME_BANK_ID,
            PaymentMethod.SPECIFIC_BANKS_ID,
            PaymentMethod.CHASE_QUICK_PAY_ID,
            PaymentMethod.POPMONEY_ID,
            PaymentMethod.MONEY_BEAM_ID,
            PaymentMethod.UPHOLD_ID,
        ]

# ///////////////////////////////////////////////////////////////////////////////////////////
# // Initialize static fields
# ///////////////////////////////////////////////////////////////////////////////////////////

# populate PAYMENT_METHODS
PaymentMethod.OK_PAY = PaymentMethod.get_dummy_payment_method(PaymentMethod.OK_PAY_ID)
PaymentMethod.CASH_APP = PaymentMethod.get_dummy_payment_method(PaymentMethod.CASH_APP_ID)
PaymentMethod.VENMO = PaymentMethod.get_dummy_payment_method(PaymentMethod.VENMO_ID)

# populate PAYMENT_METHODS
PaymentMethod.PAYMENT_METHODS = tuple(sorted([
    # EUR
    PaymentMethod(PaymentMethod.SEPA_ID, 6 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.SEPA_INSTANT_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.MONEY_BEAM_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # UK
    PaymentMethod(PaymentMethod.FASTER_PAYMENTS_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # Sweden
    PaymentMethod(PaymentMethod.SWISH_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),

    # US
    PaymentMethod(PaymentMethod.CLEAR_X_CHANGE_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    PaymentMethod(PaymentMethod.POPMONEY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.US_POSTAL_MONEY_ORDER_ID, 8 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # Canada
    PaymentMethod(PaymentMethod.INTERAC_E_TRANSFER_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # Global
    PaymentMethod(PaymentMethod.CASH_DEPOSIT_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.CASH_BY_MAIL_ID, 8 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.MONEY_GRAM_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_MID_RISK),
    PaymentMethod(PaymentMethod.WESTERN_UNION_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_MID_RISK),
    PaymentMethod(PaymentMethod.NATIONAL_BANK_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.SAME_BANK_ID, 2 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.SPECIFIC_BANKS_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.HAL_CASH_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),
    PaymentMethod(PaymentMethod.F2F_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),
    PaymentMethod(PaymentMethod.AMAZON_GIFT_CARD_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # Trans national
    PaymentMethod(PaymentMethod.UPHOLD_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.REVOLUT_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.PERFECT_MONEY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),
    PaymentMethod(PaymentMethod.ADVANCED_CASH_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_VERY_LOW_RISK),
    PaymentMethod(PaymentMethod.TRANSFERWISE_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.TRANSFERWISE_USD_ID, 4 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.PAYSERA_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.PAXUM_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.NEFT_ID, PaymentMethod.DAY_MS, Coin.parse_coin("0.02")),
    PaymentMethod(PaymentMethod.RTGS_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.IMPS_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.UPI_ID, PaymentMethod.DAY_MS, Coin.parse_coin("0.05")),
    PaymentMethod(PaymentMethod.PAYTM_ID, PaymentMethod.DAY_MS, Coin.parse_coin("0.05")),
    PaymentMethod(PaymentMethod.NEQUI_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.BIZUM_ID, PaymentMethod.DAY_MS, Coin.parse_coin("0.04")),
    PaymentMethod(PaymentMethod.PIX_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.CAPITUAL_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.CELPAY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.MONESE_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.SATISPAY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.TIKKIE_ID, PaymentMethod.DAY_MS, Coin.parse_coin("0.05")),
    PaymentMethod(PaymentMethod.VERSE_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.STRIKE_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.SWIFT_ID, 7 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_MID_RISK),
    PaymentMethod(PaymentMethod.ACH_TRANSFER_ID, 5 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),
    PaymentMethod(PaymentMethod.DOMESTIC_WIRE_TRANSFER_ID, 3 * PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # Japan
    PaymentMethod(PaymentMethod.JAPAN_BANK_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),

    # Australia
    PaymentMethod(PaymentMethod.AUSTRALIA_PAYID_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),

    # Argentina
    PaymentMethod(PaymentMethod.MERCADO_PAGO_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # China
    PaymentMethod(PaymentMethod.ALI_PAY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),
    PaymentMethod(PaymentMethod.WECHAT_PAY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),

    # Thailand
    PaymentMethod(PaymentMethod.PROMPT_PAY_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_LOW_RISK),

    # Russia
    PaymentMethod(PaymentMethod.SBP_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_HIGH_RISK),

    # Altcoins
    PaymentMethod(PaymentMethod.BLOCK_CHAINS_ID, PaymentMethod.DAY_MS, PaymentMethod.DEFAULT_TRADE_LIMIT_VERY_LOW_RISK),
    # Altcoins with 1 hour trade period
    PaymentMethod(PaymentMethod.BLOCK_CHAINS_INSTANT_ID, int(timedelta(hours=1).total_seconds()*1000), PaymentMethod.DEFAULT_TRADE_LIMIT_VERY_LOW_RISK),
    # BsqSwap
    PaymentMethod(PaymentMethod.BSQ_SWAP_ID, 1, PaymentMethod.DEFAULT_TRADE_LIMIT_VERY_LOW_RISK)
], key=lambda m: "ZELLE" if m.id == PaymentMethod.CLEAR_X_CHANGE_ID else m.id))

PaymentMethod.PAYMENT_METHOD_MAP = MappingProxyType({m.id: m for m in PaymentMethod.PAYMENT_METHODS})