
from enum import IntEnum, auto

# This enum must not change the order as we use the ordinal for storage to reduce data size.
# The payment method string can be quite long and would consume 15% more space.
# When we get a new payment method we can add it to the enum at the end. Old users would add it as string if not
# recognized.
class TradeStatistics3PaymentMethodWrapper(IntEnum):

    def _generate_next_value_(name, start, count, last_values):
        return count  # count starts from 0
    
    OK_PAY = auto()
    CASH_APP = auto()
    VENMO = auto()
    AUSTRALIA_PAYID = auto()
    UPHOLD = auto()
    MONEY_BEAM = auto()
    POPMONEY = auto()
    REVOLUT = auto()
    PERFECT_MONEY = auto()
    SEPA = auto()
    SEPA_INSTANT = auto()
    FASTER_PAYMENTS = auto()
    NATIONAL_BANK = auto()
    JAPAN_BANK = auto()
    SAME_BANK = auto()
    SPECIFIC_BANKS = auto()
    SWISH = auto()
    ALI_PAY = auto()
    WECHAT_PAY = auto()
    CLEAR_X_CHANGE = auto()
    CHASE_QUICK_PAY = auto()
    INTERAC_E_TRANSFER = auto()
    US_POSTAL_MONEY_ORDER = auto()
    CASH_DEPOSIT = auto()
    MONEY_GRAM = auto()
    WESTERN_UNION = auto()
    HAL_CASH = auto()
    F2F = auto()
    BLOCK_CHAINS = auto()
    PROMPT_PAY = auto()
    ADVANCED_CASH = auto()
    BLOCK_CHAINS_INSTANT = auto()
    TRANSFERWISE = auto()
    AMAZON_GIFT_CARD = auto()
    CASH_BY_MAIL = auto()
    CAPITUAL = auto()
    PAYSERA = auto()
    PAXUM = auto()
    SWIFT = auto()
    NEFT = auto()
    RTGS = auto()
    IMPS = auto()
    UPI = auto()
    PAYTM = auto()
    CELPAY = auto()
    NEQUI = auto()
    BIZUM = auto()
    PIX = auto()
    MONESE = auto()
    SATISPAY = auto()
    VERSE = auto()
    STRIKE = auto()
    TIKKIE = auto()
    TRANSFERWISE_USD = auto()
    ACH_TRANSFER = auto()
    DOMESTIC_WIRE_TRANSFER = auto()
    SBP = auto()
