from typing import TYPE_CHECKING
from bisq.core.payment.advanced_cash_account import AdvancedCashAccount
from bisq.core.payment.ali_pay_account import AliPayAccount
from bisq.core.payment.amazon_gift_card_account import AmazonGiftCardAccount
from bisq.core.payment.australia_payid_account import AustraliaPayidAccount
from bisq.core.payment.bsq_swap_account import BsqSwapAccount
from bisq.core.payment.cash_by_mail_account import CashByMailAccount
from bisq.core.payment.cash_deposit_account import CashDepositAccount
from bisq.core.payment.chase_quick_pay_account import ChaseQuickPayAccount
from bisq.core.payment.clear_xchange_account import ClearXchangeAccount
from bisq.core.payment.crypto_currency_account import CryptoCurrencyAccount
from bisq.core.payment.f2f_account import F2FAccount
from bisq.core.payment.faster_payments_account import FasterPaymentsAccount
from bisq.core.payment.hal_cash_account import HalCashAccount
from bisq.core.payment.imps_account import ImpsAccount
from bisq.core.payment.interac_e_transfer_account import InteracETransferAccount
from bisq.core.payment.japan_bank_account import JapanBankAccount
from bisq.core.payment.money_beam_account import MoneyBeamAccount
from bisq.core.payment.money_gram_account import MoneyGramAccount
from bisq.core.payment.national_bank_account import NationalBankAccount
from bisq.core.payment.neft_account import NeftAccount
from bisq.core.payment.paxum_account import PaxumAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.paysera_account import PayseraAccount
from bisq.core.payment.paytm_account import PaytmAccount
from bisq.core.payment.perfect_money_account import PerfectMoneyAccount
from bisq.core.payment.popmoney_account import PopmoneyAccount
from bisq.core.payment.prompt_pay_account import PromptPayAccount
from bisq.core.payment.revolute_account import RevolutAccount
from bisq.core.payment.rtgs_account import RtgsAccount
from bisq.core.payment.same_bank_account import SameBankAccount
from bisq.core.payment.sepa_account import SepaAccount
from bisq.core.payment.sepa_instant_account import SepaInstantAccount
from bisq.core.payment.specific_banks_account import SpecificBanksAccount
from bisq.core.payment.swift_account import SwiftAccount
from bisq.core.payment.swish_account import SwishAccount
from bisq.core.payment.transferwise_account import TransferwiseAccount
from bisq.core.payment.transferwise_usd_account import TransferwiseUsdAccount
from bisq.core.payment.uphold_account import UpholdAccount
from bisq.core.payment.upi_account import UpiAccount
from bisq.core.payment.us_postal_money_order_account import USPostalMoneyOrderAccount
from bisq.core.payment.we_chat_pay_account import WeChatPayAccount
from bisq.core.payment.western_union_account import WesternUnionAccount

if TYPE_CHECKING:
    from bisq.core.payment.payment_account import PaymentAccount

# TODO: not complete

_account_map = {
    PaymentMethod.UPHOLD_ID: lambda: UpholdAccount(),
    PaymentMethod.MONEY_BEAM_ID: lambda: MoneyBeamAccount(),
    PaymentMethod.POPMONEY_ID: lambda: PopmoneyAccount(),
    PaymentMethod.REVOLUT_ID: lambda: RevolutAccount(),
    PaymentMethod.PERFECT_MONEY_ID: lambda: PerfectMoneyAccount(),
    PaymentMethod.SEPA_ID: lambda: SepaAccount(),
    PaymentMethod.SEPA_INSTANT_ID: lambda: SepaInstantAccount(),
    PaymentMethod.FASTER_PAYMENTS_ID: lambda: FasterPaymentsAccount(),
    PaymentMethod.NATIONAL_BANK_ID: lambda: NationalBankAccount(),
    PaymentMethod.SAME_BANK_ID: lambda: SameBankAccount(),
    PaymentMethod.SPECIFIC_BANKS_ID: lambda: SpecificBanksAccount(),
    PaymentMethod.JAPAN_BANK_ID: lambda: JapanBankAccount(),
    PaymentMethod.AUSTRALIA_PAYID_ID: lambda: AustraliaPayidAccount(),
    PaymentMethod.ALI_PAY_ID: lambda: AliPayAccount(),
    PaymentMethod.WECHAT_PAY_ID: lambda: WeChatPayAccount(),
    PaymentMethod.SWISH_ID: lambda: SwishAccount(),
    PaymentMethod.CLEAR_X_CHANGE_ID: lambda: ClearXchangeAccount(),
    PaymentMethod.CHASE_QUICK_PAY_ID: lambda: ChaseQuickPayAccount(),
    PaymentMethod.INTERAC_E_TRANSFER_ID: lambda: InteracETransferAccount(),
    PaymentMethod.US_POSTAL_MONEY_ORDER_ID: lambda: USPostalMoneyOrderAccount(),
    PaymentMethod.CASH_DEPOSIT_ID: lambda: CashDepositAccount(),
    PaymentMethod.BLOCK_CHAINS_ID: lambda: CryptoCurrencyAccount(),
    PaymentMethod.MONEY_GRAM_ID: lambda: MoneyGramAccount(),
    PaymentMethod.WESTERN_UNION_ID: lambda: WesternUnionAccount(),
    PaymentMethod.HAL_CASH_ID: lambda: HalCashAccount(),
    PaymentMethod.F2F_ID: lambda: F2FAccount(),
    PaymentMethod.CASH_BY_MAIL_ID: lambda: CashByMailAccount(),
    PaymentMethod.PROMPT_PAY_ID: lambda: PromptPayAccount(),
    PaymentMethod.ADVANCED_CASH_ID: lambda: AdvancedCashAccount(),
    PaymentMethod.TRANSFERWISE_ID: lambda: TransferwiseAccount(),
    PaymentMethod.TRANSFERWISE_USD_ID: lambda: TransferwiseUsdAccount(),
    PaymentMethod.PAYSERA_ID: lambda: PayseraAccount(),
    PaymentMethod.PAXUM_ID: lambda: PaxumAccount(),
    PaymentMethod.NEFT_ID: lambda: NeftAccount(),
    PaymentMethod.RTGS_ID: lambda: RtgsAccount(),
    PaymentMethod.IMPS_ID: lambda: ImpsAccount(),
    PaymentMethod.UPI_ID: lambda: UpiAccount(),
    PaymentMethod.PAYTM_ID: lambda: PaytmAccount(),
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
    PaymentMethod.BSQ_SWAP_ID: lambda: BsqSwapAccount(),
    # PaymentMethod.MERCADO_PAGO_ID: lambda: MercadoPagoAccount(),
    # PaymentMethod.SBP_ID: lambda: SbpAccount(),
    # Cannot be deleted as it would break old trade history entries
    # PaymentMethod.OK_PAY_ID: lambda: OKPayAccount(),
    # PaymentMethod.CASH_APP_ID: lambda: CashAppAccount(),
    # PaymentMethod.VENMO_ID: lambda: VenmoAccount(),
}


class PaymentAccountFactory:

    @staticmethod
    def get_payment_account(payment_method: "PaymentMethod") -> "PaymentAccount":
        try:
            return _account_map[payment_method.id]()
        except KeyError:
            raise RuntimeError(f"Not supported PaymentMethod: {payment_method}")
