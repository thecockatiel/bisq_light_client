from typing import TYPE_CHECKING
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.sepa_account import SepaAccount
from bisq.core.payment.sepa_instant_account import SepaInstantAccount
from bisq.core.payment.swift_account import SwiftAccount

if TYPE_CHECKING:
    from bisq.core.payment.payment_account import PaymentAccount

# TODO: not complete

class PaymentAccountFactory():
    
    @staticmethod
    def get_payment_account(payment_method: "PaymentMethod") -> "PaymentAccount":
        match payment_method.id:
            # case PaymentMethod.UPHOLD_ID:
            #     return UpholdAccount()
            # case PaymentMethod.MONEY_BEAM_ID:
            #     return MoneyBeamAccount()
            # case PaymentMethod.POPMONEY_ID:
            #     return PopmoneyAccount()
            # case PaymentMethod.REVOLUT_ID:
            #     return RevolutAccount()
            # case PaymentMethod.PERFECT_MONEY_ID:
            #     return PerfectMoneyAccount()
            case PaymentMethod.SEPA_ID:
                return SepaAccount()
            case PaymentMethod.SEPA_INSTANT_ID:
                return SepaInstantAccount()
            # case PaymentMethod.FASTER_PAYMENTS_ID:
            #     return FasterPaymentsAccount()
            # case PaymentMethod.NATIONAL_BANK_ID:
            #     return NationalBankAccount()
            # case PaymentMethod.SAME_BANK_ID:
            #     return SameBankAccount()
            # case PaymentMethod.SPECIFIC_BANKS_ID:
            #     return SpecificBanksAccount()
            # case PaymentMethod.JAPAN_BANK_ID:
            #     return JapanBankAccount()
            # case PaymentMethod.AUSTRALIA_PAYID_ID:
            #     return AustraliaPayidAccount()
            # case PaymentMethod.ALI_PAY_ID:
            #     return AliPayAccount()
            # case PaymentMethod.WECHAT_PAY_ID:
            #     return WeChatPayAccount()
            # case PaymentMethod.SWISH_ID:
            #     return SwishAccount()
            # case PaymentMethod.CLEAR_X_CHANGE_ID:
            #     return ClearXchangeAccount()
            # case PaymentMethod.CHASE_QUICK_PAY_ID:
            #     return ChaseQuickPayAccount()
            # case PaymentMethod.INTERAC_E_TRANSFER_ID:
            #     return InteracETransferAccount()
            # case PaymentMethod.US_POSTAL_MONEY_ORDER_ID:
            #     return USPostalMoneyOrderAccount()
            # case PaymentMethod.CASH_DEPOSIT_ID:
            #     return CashDepositAccount()
            # case PaymentMethod.BLOCK_CHAINS_ID:
            #     return CryptoCurrencyAccount()
            # case PaymentMethod.MONEY_GRAM_ID:
            #     return MoneyGramAccount()
            # case PaymentMethod.WESTERN_UNION_ID:
            #     return WesternUnionAccount()
            # case PaymentMethod.HAL_CASH_ID:
            #     return HalCashAccount()
            # case PaymentMethod.F2F_ID:
            #     return F2FAccount()
            # case PaymentMethod.CASH_BY_MAIL_ID:
            #     return CashByMailAccount()
            # case PaymentMethod.PROMPT_PAY_ID:
            #     return PromptPayAccount()
            # case PaymentMethod.ADVANCED_CASH_ID:
            #     return AdvancedCashAccount()
            # case PaymentMethod.TRANSFERWISE_ID:
            #     return TransferwiseAccount()
            # case PaymentMethod.TRANSFERWISE_USD_ID:
            #     return TransferwiseUsdAccount()
            # case PaymentMethod.PAYSERA_ID:
            #     return PayseraAccount()
            # case PaymentMethod.PAXUM_ID:
            #     return PaxumAccount()
            # case PaymentMethod.NEFT_ID:
            #     return NeftAccount()
            # case PaymentMethod.RTGS_ID:
            #     return RtgsAccount()
            # case PaymentMethod.IMPS_ID:
            #     return ImpsAccount()
            # case PaymentMethod.UPI_ID:
            #     return UpiAccount()
            # case PaymentMethod.PAYTM_ID:
            #     return PaytmAccount()
            # case PaymentMethod.NEQUI_ID:
            #     return NequiAccount()
            # case PaymentMethod.BIZUM_ID:
            #     return BizumAccount()
            # case PaymentMethod.PIX_ID:
            #     return PixAccount()
            # case PaymentMethod.AMAZON_GIFT_CARD_ID:
            #     return AmazonGiftCardAccount()
            # case PaymentMethod.BLOCK_CHAINS_INSTANT_ID:
            #     return InstantCryptoCurrencyAccount()
            # case PaymentMethod.CAPITUAL_ID:
            #     return CapitualAccount()
            # case PaymentMethod.CELPAY_ID:
            #     return CelPayAccount()
            # case PaymentMethod.MONESE_ID:
            #     return MoneseAccount()
            # case PaymentMethod.SATISPAY_ID:
            #     return SatispayAccount()
            # case PaymentMethod.TIKKIE_ID:
            #     return TikkieAccount()
            # case PaymentMethod.VERSE_ID:
            #     return VerseAccount()
            # case PaymentMethod.STRIKE_ID:
            #     return StrikeAccount()
            case PaymentMethod.SWIFT_ID:
                return SwiftAccount()
            # case PaymentMethod.ACH_TRANSFER_ID:
            #     return AchTransferAccount()
            # case PaymentMethod.DOMESTIC_WIRE_TRANSFER_ID:
            #     return DomesticWireTransferAccount()
            # case PaymentMethod.BSQ_SWAP_ID:
            #     return BsqSwapAccount()
            # case PaymentMethod.MERCADO_PAGO_ID:
            #     return MercadoPagoAccount()
            
            # Cannot be deleted as it would break old trade history entries
            # case PaymentMethod.OK_PAY_ID:
            #     return OKPayAccount()
            # case PaymentMethod.CASH_APP_ID:
            #     return CashAppAccount()
            # case PaymentMethod.VENMO_ID:
            #     return VenmoAccount()
            
            case _:
                raise RuntimeError(f"Not supported PaymentMethod: {payment_method}")
