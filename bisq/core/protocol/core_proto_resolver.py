from collections.abc import Callable
from dataclasses import dataclass
from typing import Union

from bisq.common.protocol.proto_resolver import ProtoResolver
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.account.witness.account_age_witness import AccountAgeWitness
from bisq.core.dao.governance.blindvote.storage.blind_vote_payload import BlindVotePayload
from bisq.core.dao.governance.proposal.storage.appendonly.proposal_payload import ProposalPayload
from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
from bisq.core.payment.payload.ach_transfer_account_payload import AchTransferAccountPayload
from bisq.core.payment.payload.advanced_cash_account_payload import AdvancedCashAccountPayload
from bisq.core.payment.payload.ali_pay_account_payload import AliPayAccountPayload
from bisq.core.payment.payload.amazon_gift_card_account_payload import AmazonGiftCardAccountPayload
from bisq.core.payment.payload.australia_payid_account_payload import AustraliaPayidAccountPayload
from bisq.core.payment.payload.bizum_account_payload import BizumAccountPayload
from bisq.core.payment.payload.bsq_swap_account_payload import BsqSwapAccountPayload
from bisq.core.payment.payload.capitual_account_payload import CapitualAccountPayload
from bisq.core.payment.payload.cash_app_account_payload import CashAppAccountPayload
from bisq.core.payment.payload.cash_by_mail_account_payload import CashByMailAccountPayload
from bisq.core.payment.payload.cash_deposit_account_payload import CashDepositAccountPayload
from bisq.core.payment.payload.cel_pay_account_payload import CelPayAccountPayload
from bisq.core.payment.payload.chase_quick_pay_account_payload import ChaseQuickPayAccountPayload
from bisq.core.payment.payload.clear_xchange_account_payload import ClearXchangeAccountPayload
from bisq.core.payment.payload.crypto_currency_account_payload import CryptoCurrencyAccountPayload
from bisq.core.payment.payload.domestic_wire_transfer_account_payload import DomesticWireTransferAccountPayload
from bisq.core.payment.payload.f2f_account_payload import F2FAccountPayload
from bisq.core.payment.payload.faster_payments_account_payload import FasterPaymentsAccountPayload
from bisq.core.payment.payload.hal_cash_account_payload import HalCashAccountPayload
from bisq.core.payment.payload.imps_account_payload import ImpsAccountPayload
from bisq.core.payment.payload.instant_crypto_currency_account_payload import InstantCryptoCurrencyPayload
from bisq.core.payment.payload.interac_e_transfer_account_payload import InteracETransferAccountPayload
from bisq.core.payment.payload.japan_bank_account_payload import JapanBankAccountPayload
from bisq.core.payment.payload.mercado_pago_account_payload import MercadoPagoAccountPayload
from bisq.core.payment.payload.monese_account_payload import MoneseAccountPayload
from bisq.core.payment.payload.money_beam_account_payload import MoneyBeamAccountPayload
from bisq.core.payment.payload.money_gram_account_payload import MoneyGramAccountPayload
from bisq.core.payment.payload.national_bank_account_payload import NationalBankAccountPayload
from bisq.core.payment.payload.neft_account_payload import NeftAccountPayload
from bisq.core.payment.payload.nequi_account_payload import NequiAccountPayload
from bisq.core.payment.payload.ok_pay_account_payload import OKPayAccountPayload
from bisq.core.payment.payload.paxum_account_payload import PaxumAccountPayload
from bisq.core.payment.payload.paysera_account_payload import PayseraAccountPayload
from bisq.core.payment.payload.paytm_account_payload import PaytmAccountPayload
from bisq.core.payment.payload.perfect_money_account_payload import PerfectMoneyAccountPayload
from bisq.core.payment.payload.pix_account_payload import PixAccountPayload
from bisq.core.payment.payload.popmoney_account_payload import PopmoneyAccountPayload
from bisq.core.payment.payload.prompt_pay_account_payload import PromptPayAccountPayload
from bisq.core.payment.payload.revolute_account_payload import RevolutAccountPayload
from bisq.core.payment.payload.rtgs_account_payload import RtgsAccountPayload
from bisq.core.payment.payload.same_bank_account_payload import SameBankAccountPayload
from bisq.core.payment.payload.satispay_account_payload import SatispayAccountPayload
from bisq.core.payment.payload.sbp_account_payload import SbpAccountPayload
from bisq.core.payment.payload.sepa_account_payload import SepaAccountPayload
from bisq.core.payment.payload.sepa_instant_account_payload import SepaInstantAccountPayload
from bisq.core.payment.payload.specfic_banks_account_payload import SpecificBanksAccountPayload
from bisq.core.payment.payload.strike_account_payload import StrikeAccountPayload
from bisq.core.payment.payload.swift_account_payload import SwiftAccountPayload
from bisq.core.payment.payload.swish_account_payload import SwishAccountPayload
from bisq.core.payment.payload.tikkie_account_payload import TikkieAccountPayload
from bisq.core.payment.payload.transferwise_account_payload import TransferwiseAccountPayload
from bisq.core.payment.payload.transferwise_usd_account_payload import TransferwiseUsdAccountPayload
from bisq.core.payment.payload.uphold_account_payload import UpholdAccountPayload
from bisq.core.payment.payload.upi_account_payload import UpiAccountPayload
from bisq.core.payment.payload.us_postal_money_order_account_payload import USPostalMoneyOrderAccountPayload
from bisq.core.payment.payload.venmo_account_payload import VenmoAccountPayload
from bisq.core.payment.payload.verse_account_payload import VerseAccountPayload
from bisq.core.payment.payload.we_chat_pay_account_payload import WeChatPayAccountPayload
from bisq.core.payment.payload.western_union_account_payload import WesternUnionAccountPayload
from bisq.core.trade.statistics.trade_statistics_2 import TradeStatistics2
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3
from utils.clock import Clock

import pb_pb2 as protobuf


def _handle_country_based_payment_account_payload(proto: "protobuf.PaymentAccountPayload"):
    handler = country_based_payment_account_payload_cases.get(proto.country_based_payment_account_payload.WhichOneof("message"), None)
    if handler:
        return handler(proto)
    else:
        raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload.CountryBasedPaymentAccountPayload). messageCase=" + proto.country_based_payment_account_payload.WhichOneof("message"))

def _handle_bank_account_payload(proto: "protobuf.PaymentAccountPayload"):
    handler = bank_account_payload_cases.get(proto.country_based_payment_account_payload.bank_account_payload.WhichOneof("message"), None)
    if handler:
        return handler(proto)
    else:
        raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload.CountryBasedPaymentAccountPayload.BankAccountPayload). messageCase=" + proto.country_based_payment_account_payload.bank_account_payload.WhichOneof("message"))

def _handle_ifsc_based_account_payload(proto: "protobuf.PaymentAccountPayload"):
    handler = ifsc_based_account_payload_cases.get(proto.country_based_payment_account_payload.ifsc_based_account_payload.WhichOneof("message"), None)
    if handler:
        return handler(proto)
    else:
        raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload.CountryBasedPaymentAccountPayload.IfscBasedPaymentAccount). messageCase=" + proto.country_based_payment_account_payload.ifsc_based_account_payload.WhichOneof("message"))

payment_account_payload_cases = {
    "ali_pay_account_payload": AliPayAccountPayload.from_proto,
    "we_chat_pay_account_payload": WeChatPayAccountPayload.from_proto,
    "chase_quick_pay_account_payload": ChaseQuickPayAccountPayload.from_proto,
    "clear_xchange_account_payload": ClearXchangeAccountPayload.from_proto,
    "country_based_payment_account_payload": _handle_country_based_payment_account_payload,
    "crypto_currency_account_payload": CryptoCurrencyAccountPayload.from_proto,
    "faster_payments_account_payload": FasterPaymentsAccountPayload.from_proto,
    "interac_e_transfer_account_payload": InteracETransferAccountPayload.from_proto,
    "japan_bank_account_payload": JapanBankAccountPayload.from_proto,
    "australia_payid_payload": AustraliaPayidAccountPayload.from_proto,
    "uphold_account_payload": UpholdAccountPayload.from_proto,
    "money_beam_account_payload": MoneyBeamAccountPayload.from_proto,
    "money_gram_account_payload": MoneyGramAccountPayload.from_proto,
    "popmoney_account_payload": PopmoneyAccountPayload.from_proto,
    "revolut_account_payload": RevolutAccountPayload.from_proto,
    "perfect_money_account_payload": PerfectMoneyAccountPayload.from_proto,
    "swish_account_payload": SwishAccountPayload.from_proto,
    "hal_cash_account_payload": HalCashAccountPayload.from_proto,
    "u_s_postal_money_order_account_payload": USPostalMoneyOrderAccountPayload.from_proto,
    "cash_by_mail_account_payload": CashByMailAccountPayload.from_proto,
    "prompt_pay_account_payload": PromptPayAccountPayload.from_proto,
    "advanced_cash_account_payload": AdvancedCashAccountPayload.from_proto,
    "transferwise_account_payload": TransferwiseAccountPayload.from_proto,
    "paysera_account_payload": PayseraAccountPayload.from_proto,
    "paxum_account_payload": PaxumAccountPayload.from_proto,
    "amazon_gift_card_account_payload": AmazonGiftCardAccountPayload.from_proto,
    "instant_crypto_currency_account_payload": InstantCryptoCurrencyPayload.from_proto,
    "capitual_account_payload": CapitualAccountPayload.from_proto,
    "cel_pay_account_payload": CelPayAccountPayload.from_proto,
    "monese_account_payload": MoneseAccountPayload.from_proto,
    "verse_account_payload": VerseAccountPayload.from_proto,
    "swift_account_payload": SwiftAccountPayload.from_proto,
    "bsq_swap_account_payload": BsqSwapAccountPayload.from_proto,
    "sbp_account_payload": SbpAccountPayload.from_proto,
    
    # Cannot be deleted as it would break old trade history entries
    "o_k_pay_account_payload": OKPayAccountPayload.from_proto,
    "cash_app_account_payload": CashAppAccountPayload.from_proto,
    "venmo_account_payload": VenmoAccountPayload.from_proto,
}

persistable_network_payload_cases: dict[str, Callable[[protobuf.PersistableNetworkPayload], PersistableNetworkPayload]] = {
    "account_age_witness": lambda proto: AccountAgeWitness.from_proto(proto.account_age_witness),
    "trade_statistics2": lambda proto: TradeStatistics2.from_proto(proto.trade_statistics2),
    "proposal_payload": lambda proto: ProposalPayload.from_proto(proto.proposal_payload),
    "blind_vote_payload": lambda proto: BlindVotePayload.from_proto(proto.blind_vote_payload),
    "signed_witness": lambda proto: SignedWitness.from_proto(proto.signed_witness),
    "trade_statistics3": lambda proto: TradeStatistics3.from_proto(proto.trade_statistics3),
}

country_based_payment_account_payload_cases = {
    "bank_account_payload": _handle_bank_account_payload,
    "western_union_account_payload": WesternUnionAccountPayload.from_proto,
    "cash_deposit_account_payload": CashDepositAccountPayload.from_proto,
    "sepa_account_payload": SepaAccountPayload.from_proto,
    "sepa_instant_account_payload": SepaInstantAccountPayload.from_proto,
    "f2f_account_payload": F2FAccountPayload.from_proto,
    "upi_account_payload": UpiAccountPayload.from_proto,
    "paytm_account_payload": PaytmAccountPayload.from_proto,
    "nequi_account_payload": NequiAccountPayload.from_proto,
    "bizum_account_payload": BizumAccountPayload.from_proto,
    "pix_account_payload": PixAccountPayload.from_proto,
    "satispay_account_payload": SatispayAccountPayload.from_proto,
    "tikkie_account_payload": TikkieAccountPayload.from_proto,
    "strike_account_payload": StrikeAccountPayload.from_proto,
    "transferwise_usd_account_payload": TransferwiseUsdAccountPayload.from_proto,
    "mercado_pago_account_payload": MercadoPagoAccountPayload.from_proto,
    "ifsc_based_account_payload": _handle_ifsc_based_account_payload,
}

bank_account_payload_cases = {
    "national_bank_account_payload": NationalBankAccountPayload.from_proto,
    "same_bank_accunt_payload": SameBankAccountPayload.from_proto,
    "specific_banks_account_payload": SpecificBanksAccountPayload.from_proto,
    "ach_transfer_account_payload": AchTransferAccountPayload.from_proto,
    "domestic_wire_transfer_account_payload": DomesticWireTransferAccountPayload.from_proto,
}

ifsc_based_account_payload_cases = {
    "neft_account_payload": NeftAccountPayload.from_proto,
    "rtgs_account_payload": RtgsAccountPayload.from_proto,
    "imps_account_payload": ImpsAccountPayload.from_proto,
}

@dataclass
class CoreProtoResolver(ProtoResolver):
    clock: Clock

    def __post_init__(self):
        self.logger = get_ctx_logger(__name__)
    
    def from_proto(self, proto: Union['protobuf.PaymentAccountPayload','protobuf.PersistableNetworkPayload']):
        if proto is None:
            self.logger.error("CoreProtoResolver.fromProto: proto is null")
            raise ProtobufferException("proto is null")
        
        if isinstance(proto, protobuf.PaymentAccountPayload):
            handler = payment_account_payload_cases.get(proto.WhichOneof("message"), None)
            if handler:
                return handler(proto)
            else:
                raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload). messageCase=" + proto.WhichOneof("message"))
        elif isinstance(proto, protobuf.PersistableNetworkPayload):
            handler = persistable_network_payload_cases.get(proto.WhichOneof("message"), None)
            if handler:
                return handler(proto)
            else:
                raise ProtobufferException(f"Unknown proto message case (PB.PersistableNetworkPayload). messageCase={proto.WhichOneof('message')}")
        else:
            raise ProtobufferException("Unknown proto message case. proto=" + proto)
