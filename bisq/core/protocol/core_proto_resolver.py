from dataclasses import dataclass, field
from typing import Union

from bisq.common.protocol.proto_resolver import ProtoResolver
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.common.setup.log_setup import get_logger
from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.account.witness.account_age_witness import AccountAgeWitness
from bisq.core.payment.payload.amazon_gift_card_account_payload import AmazonGiftCardAccountPayload
from bisq.core.payment.payload.cash_by_mail_account_payload import CashByMailAccountPayload
from bisq.core.payment.payload.f2f_account_payload import F2FAccountPayload
from bisq.core.payment.payload.same_bank_account_payload import SameBankAccountPayload
from bisq.core.payment.payload.sepa_account_payload import SepaAccountPayload
from bisq.core.payment.payload.sepa_instant_account_payload import SepaInstantAccountPayload
from bisq.core.payment.payload.specfic_banks_account_payload import SpecificBanksAccountPayload
from utils.clock import Clock

import proto.pb_pb2 as protobuf

logger = get_logger(__name__)

@dataclass
class CoreProtoResolver(ProtoResolver):
    clock: Clock
    
    def from_proto(self, proto: Union['protobuf.PaymentAccountPayload','protobuf.PersistableNetworkPayload']):
        if proto is None:
            logger.error("CoreProtoResolver.fromProto: proto is null")
            raise ProtobufferException("proto is null")
        
        if isinstance(proto, protobuf.PaymentAccountPayload):
            match proto.WhichOneof("message"):
                # case "ali_pay_account_payload":
                    # return AliPayAccountPayload.from_proto(proto)
                # case "we_chat_pay_account_payload":
                    # return WeChatPayAccountPayload.from_proto(proto)
                # case "chase_quick_pay_account_payload":
                    # return ChaseQuickPayAccountPayload.from_proto(proto)
                # case "clear_xchange_account_payload":
                    # return ClearXchangeAccountPayload.from_proto(proto)
                case "country_based_payment_account_payload":
                    match proto.country_based_payment_account_payload.WhichOneof("message"):
                        case "bank_account_payload":
                            match proto.country_based_payment_account_payload.bank_account_payload.WhichOneof("message"):
                                # case "national_bank_account_payload":
                                    # return NationalBankAccountPayload.from_proto(proto)
                                case "same_bank_accunt_payload":
                                    return SameBankAccountPayload.from_proto(proto)
                                case "specific_banks_account_payload":
                                    return SpecificBanksAccountPayload.from_proto(proto)
                                # case "ach_transfer_account_payload":
                                    # return AchTransferAccountPayload.from_proto(proto)
                                # case "domestic_wire_transfer_account_payload":
                                    # return DomesticWireTransferAccountPayload.from_proto(proto)
                                case _:
                                    raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload.CountryBasedPaymentAccountPayload.BankAccountPayload). messageCase=" + proto.country_based_payment_account_payload.bank_account_payload.WhichOneof("message"))
                        # case "western_union_account_payload":
                            # return WesternUnionAccountPayload.from_proto(proto)
                        # case "cash_deposit_account_payload":
                            # return CashDepositAccountPayload.from_proto(proto)
                        case "sepa_account_payload":
                            return SepaAccountPayload.from_proto(proto)
                        case "sepa_instant_account_payload":
                            return SepaInstantAccountPayload.from_proto(proto)
                        case "f2f_account_payload":
                            return F2FAccountPayload.from_proto(proto)
                        # case "upi_account_payload":
                            # return UpiAccountPayload.from_proto(proto)
                        # case "paytm_account_payload":
                            # return PaytmAccountPayload.from_proto(proto)
                        # case "nequi_account_payload":
                            # return NequiAccountPayload.from_proto(proto)
                        # case "bizum_account_payload":
                            # return BizumAccountPayload.from_proto(proto)
                        # case "pix_account_payload":
                            # return PixAccountPayload.from_proto(proto)
                        # case "satispay_account_payload":
                            # return SatispayAccountPayload.from_proto(proto)
                        # case "tikkie_account_payload":
                            # return TikkieAccountPayload.from_proto(proto)
                        # case "strike_account_payload":
                            # return StrikeAccountPayload.from_proto(proto)
                        # case "transferwise_usd_account_payload":
                            # return TransferwiseUsdAccountPayload.from_proto(proto)
                        # case "mercado_pago_account_payload":
                            # return MercadoPagoAccountPayload.from_proto(proto)
                        case "ifsc_based_account_payload":
                            match proto.country_based_payment_account_payload.ifsc_based_account_payload.WhichOneof("message"):
                                # case "neft_account_payload":
                                    # return NeftAccountPayload.from_proto(proto)
                                # case "rtgs_account_payload":
                                    # return RtgsAccountPayload.from_proto(proto)
                                # case "imps_account_payload":
                                    # return ImpsAccountPayload.from_proto(proto)
                                case _:
                                    raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload.CountryBasedPaymentAccountPayload.IfscBasedPaymentAccount). messageCase=" + proto.country_based_payment_account_payload.ifsc_based_account_payload.WhichOneof("message"))
                        case _:
                            raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload.CountryBasedPaymentAccountPayload). messageCase=" + proto.country_based_payment_account_payload.WhichOneof("message"))
                # case "crypto_currency_account_payload":
                    # return CryptoCurrencyAccountPayload.from_proto(proto)
                # case "faster_payments_account_payload":
                    # return FasterPaymentsAccountPayload.from_proto(proto)
                # case "interac_e_transfer_account_payload":
                    # return InteracETransferAccountPayload.from_proto(proto)
                # case "japan_bank_account_payload":
                    # return JapanBankAccountPayload.from_proto(proto)
                # case "australia_payid_payload":
                    # return AustraliaPayidAccountPayload.from_proto(proto)
                # case "uphold_account_payload":
                    # return UpholdAccountPayload.from_proto(proto)
                # case "money_beam_account_payload":
                    # return MoneyBeamAccountPayload.from_proto(proto)
                # case "money_gram_account_payload":
                    # return MoneyGramAccountPayload.from_proto(proto)
                # case "popmoney_account_payload":
                    # return PopmoneyAccountPayload.from_proto(proto)
                # case "revolut_account_payload":
                    # return RevolutAccountPayload.from_proto(proto)
                # case "perfect_money_account_payload":
                    # return PerfectMoneyAccountPayload.from_proto(proto)
                # case "swish_account_payload":
                    # return SwishAccountPayload.from_proto(proto)
                # case "hal_cash_account_payload":
                    # return HalCashAccountPayload.from_proto(proto)
                # case "u_s_postal_money_order_account_payload":
                    # return USPostalMoneyOrderAccountPayload.from_proto(proto)
                case "cash_by_mail_account_payload":
                    return CashByMailAccountPayload.from_proto(proto)
                # case "prompt_pay_account_payload":
                    # return PromptPayAccountPayload.from_proto(proto)
                # case "advanced_cash_account_payload":
                    # return AdvancedCashAccountPayload.from_proto(proto)
                # case "transferwise_account_payload":
                    # return TransferwiseAccountPayload.from_proto(proto)
                # case "paysera_account_payload":
                    # return PayseraAccountPayload.from_proto(proto)
                # case "paxum_account_payload":
                    # return PaxumAccountPayload.from_proto(proto)
                case "amazon_gift_card_account_payload":
                    return AmazonGiftCardAccountPayload.from_proto(proto)
                # case "instant_crypto_currency_account_payload":
                    # return InstantCryptoCurrencyPayload.from_proto(proto)
                # case "capitual_account_payload":
                    # return CapitualAccountPayload.from_proto(proto)
                # case "cel_pay_account_payload":
                    # return CelPayAccountPayload.from_proto(proto)
                # case "monese_account_payload":
                    # return MoneseAccountPayload.from_proto(proto)
                # case "verse_account_payload":
                    # return VerseAccountPayload.from_proto(proto)
                # case "swift_account_payload":
                    # return SwiftAccountPayload.from_proto(proto)
                # case "bsq_swap_account_payload":
                    # return BsqSwapAccountPayload.from_proto(proto)
                # case "sbp_account_payload":
                    # return SbpAccountPayload.from_proto(proto)
                # case "o_k_pay_account_payload":
                    # return OKPayAccountPayload.from_proto(proto)
                # case "cash_app_account_payload":
                    # return CashAppAccountPayload.from_proto(proto)
                # case "venmo_account_payload":
                    # return VenmoAccountPayload.from_proto(proto)
                case _:
                    raise ProtobufferException("Unknown proto message case (PB.PaymentAccountPayload). messageCase=" + proto.WhichOneof("message"))
        elif isinstance(proto, protobuf.PersistableNetworkPayload):
            match proto.WhichOneof("message"):
                case "account_age_witness":
                    return AccountAgeWitness.from_proto(proto.account_age_witness)
                # case "trade_statistics2":
                    # return TradeStatistics2.from_proto(proto.trade_statistics2)
                # case "proposal_payload":
                    # return ProposalPayload.from_proto(proto.proposal_payload)
                # case "blind_vote_payload":
                    # return BlindVotePayload.from_proto(proto.blind_vote_payload)
                case "signed_witness":
                    return SignedWitness.from_proto(proto.signed_witness)
                # case "trade_statistics3":
                    # return TradeStatistics3.from_proto(proto.trade_statistics3)
                case _:
                    raise ProtobufferException(f"Unknown proto message case (PB.PersistableNetworkPayload). messageCase={proto.WhichOneof('message')}")
        else:
            raise ProtobufferException("Unknown proto message type. proto=" + proto)