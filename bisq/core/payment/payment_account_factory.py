from typing import TYPE_CHECKING
from bisq.core.payment.amazon_gift_card_account import AmazonGiftCardAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.revolute_account import RevolutAccount
from bisq.core.payment.sepa_account import SepaAccount
from bisq.core.payment.sepa_instant_account import SepaInstantAccount
from bisq.core.payment.swift_account import SwiftAccount

if TYPE_CHECKING:
    from bisq.core.payment.payment_account import PaymentAccount

# TODO: not complete

class PaymentAccountFactory():
    
    @staticmethod
    def get_payment_account(payment_method: "PaymentMethod") -> "PaymentAccount":
        account_map = {
            # PaymentMethod.UPHOLD_ID: lambda: UpholdAccount(),
            # PaymentMethod.MONEY_BEAM_ID: lambda: MoneyBeamAccount(),
            # PaymentMethod.POPMONEY_ID: lambda: PopmoneyAccount(),
            PaymentMethod.REVOLUT_ID: lambda: RevolutAccount(),
            # PaymentMethod.PERFECT_MONEY_ID: lambda: PerfectMoneyAccount(),
            PaymentMethod.SEPA_ID: lambda: SepaAccount(),
            PaymentMethod.SEPA_INSTANT_ID: lambda: SepaInstantAccount(),
            # PaymentMethod.FASTER_PAYMENTS_ID: lambda: FasterPaymentsAccount(),
            # PaymentMethod.NATIONAL_BANK_ID: lambda: NationalBankAccount(),
            # PaymentMethod.SAME_BANK_ID: lambda: SameBankAccount(),
            # PaymentMethod.SPECIFIC_BANKS_ID: lambda: SpecificBanksAccount(),
            # PaymentMethod.JAPAN_BANK_ID: lambda: JapanBankAccount(),
            # PaymentMethod.AUSTRALIA_PAYID_ID: lambda: AustraliaPayidAccount(),
            # PaymentMethod.ALI_PAY_ID: lambda: AliPayAccount(),
            # PaymentMethod.WECHAT_PAY_ID: lambda: WeChatPayAccount(),
            # PaymentMethod.SWISH_ID: lambda: SwishAccount(),
            # PaymentMethod.CLEAR_X_CHANGE_ID: lambda: ClearXchangeAccount(),
            # PaymentMethod.CHASE_QUICK_PAY_ID: lambda: ChaseQuickPayAccount(),
            # PaymentMethod.INTERAC_E_TRANSFER_ID: lambda: InteracETransferAccount(),
            # PaymentMethod.US_POSTAL_MONEY_ORDER_ID: lambda: USPostalMoneyOrderAccount(),
            # PaymentMethod.CASH_DEPOSIT_ID: lambda: CashDepositAccount(),
            # PaymentMethod.BLOCK_CHAINS_ID: lambda: CryptoCurrencyAccount(),
            # PaymentMethod.MONEY_GRAM_ID: lambda: MoneyGramAccount(),
            # PaymentMethod.WESTERN_UNION_ID: lambda: WesternUnionAccount(),
            # PaymentMethod.HAL_CASH_ID: lambda: HalCashAccount(),
            # PaymentMethod.F2F_ID: lambda: F2FAccount(),
            # PaymentMethod.CASH_BY_MAIL_ID: lambda: CashByMailAccount(),
            # PaymentMethod.PROMPT_PAY_ID: lambda: PromptPayAccount(),
            # PaymentMethod.ADVANCED_CASH_ID: lambda: AdvancedCashAccount(),
            # PaymentMethod.TRANSFERWISE_ID: lambda: TransferwiseAccount(),
            # PaymentMethod.TRANSFERWISE_USD_ID: lambda: TransferwiseUsdAccount(),
            # PaymentMethod.PAYSERA_ID: lambda: PayseraAccount(),
            # PaymentMethod.PAXUM_ID: lambda: PaxumAccount(),
            # PaymentMethod.NEFT_ID: lambda: NeftAccount(),
            # PaymentMethod.RTGS_ID: lambda: RtgsAccount(),
            # PaymentMethod.IMPS_ID: lambda: ImpsAccount(),
            # PaymentMethod.UPI_ID: lambda: UpiAccount(),
            # PaymentMethod.PAYTM_ID: lambda: PaytmAccount(),
            # PaymentMethod.NEQUI_ID: lambda: NequiAccount(),
            # PaymentMethod.BIZUM_ID: lambda: BizumAccount(),
            # PaymentMethod.PIX_ID: lambda: PixAccount(),
            PaymentMethod.AMAZON_GIFT_CARD_ID: lambda: AmazonGiftCardAccount(),
            # PaymentMethod.BLOCK_CHAINS_INSTANT_ID: lambda: InstantCryptoCurrencyAccount(),
            # PaymentMethod.CAPITUAL_ID: lambda: CapitualAccount(),
            # PaymentMethod.CELPAY_ID: lambda: CelPayAccount(),
            # PaymentMethod.MONESE_ID: lambda: MoneseAccount(),
            # PaymentMethod.SATISPAY_ID: lambda: SatispayAccount(),
            # PaymentMethod.TIKKIE_ID: lambda: TikkieAccount(),
            # PaymentMethod.VERSE_ID: lambda: VerseAccount(),
            # PaymentMethod.STRIKE_ID: lambda: StrikeAccount(),
            PaymentMethod.SWIFT_ID: lambda: SwiftAccount(),
            # PaymentMethod.ACH_TRANSFER_ID: lambda: AchTransferAccount(),
            # PaymentMethod.DOMESTIC_WIRE_TRANSFER_ID: lambda: DomesticWireTransferAccount(),
            # PaymentMethod.BSQ_SWAP_ID: lambda: BsqSwapAccount(),
            # PaymentMethod.MERCADO_PAGO_ID: lambda: MercadoPagoAccount(),
            
            # Cannot be deleted as it would break old trade history entries
            # PaymentMethod.OK_PAY_ID: lambda: OKPayAccount(),
            # PaymentMethod.CASH_APP_ID: lambda: CashAppAccount(),
            # PaymentMethod.VENMO_ID: lambda: VenmoAccount(),
        }
        
        try:
            return account_map[payment_method.id]()
        except KeyError:
            raise RuntimeError(f"Not supported PaymentMethod: {payment_method}")
