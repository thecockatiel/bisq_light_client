from dataclasses import dataclass, field 
from typing import TYPE_CHECKING, Optional
from google.protobuf.message import Message
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.locale.currency_util import is_fiat_currency
from bisq.core.monetary.price import Price
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.util.json_util import JsonUtil
from bisq.core.util.string_utils import string_difference
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
import pb_pb2 as protobuf
import re

from utils.data import raise_required
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.protocol.core_proto_resolver import CoreProtoResolver
    from bisq.core.monetary.volume import Volume


@dataclass
class Contract(NetworkPayload):
    offer_payload: "OfferPayload" = field(default_factory=raise_required)
    trade_amount: int = field(default_factory=raise_required)
    trade_price: int = field(default_factory=raise_required)
    taker_fee_tx_id: str = field(default_factory=raise_required)
    buyer_node_address: "NodeAddress" = field(default_factory=raise_required)
    seller_node_address: "NodeAddress" = field(default_factory=raise_required)
    mediator_node_address: "NodeAddress" = field(default_factory=raise_required)
    is_buyer_maker_and_seller_taker: bool = field(default_factory=raise_required)
    maker_account_id: str = field(default_factory=raise_required)
    taker_account_id: str = field(default_factory=raise_required)

    # Changed in v1.7.0: Not a final field anymore but initially set to null and later once the data is transmitted
    # set via a setter. This breaks the immutability of the contract but as there are several areas where we access
    # that data it is the less painful solution.
    maker_payment_account_payload: Optional["PaymentAccountPayload"] = field(default=None)
    taker_payment_account_payload: Optional["PaymentAccountPayload"] = field(default=None)

    maker_pub_key_ring: "PubKeyRing" = field(default_factory=raise_required)  # JsonExclude
    taker_pub_key_ring: "PubKeyRing" = field(default_factory=raise_required)  # JsonExclude
    maker_payout_address_string: str = field(default_factory=raise_required)
    taker_payout_address_string: str = field(default_factory=raise_required)
    maker_multi_sig_pub_key: bytes = field(default_factory=raise_required)  # JsonExclude
    taker_multi_sig_pub_key: bytes = field(default_factory=raise_required)  # JsonExclude

    # Added in v1.2.0
    lock_time: int = field(default_factory=raise_required)
    refund_agent_node_address: "NodeAddress" = field(default_factory=raise_required)

    # Added in v1.7.0
    hash_of_makers_payment_account_payload: Optional[bytes] = field(default=None)
    hash_of_takers_payment_account_payload: Optional[bytes] = field(default=None)
    maker_payment_method_id: Optional[str] = field(default=None)
    taker_payment_method_id: Optional[str] = field(default=None)

    def __post_init__(self):
        self.logger = get_ctx_logger(__name__)
        # Either makerPaymentMethodId is set, or obtained from offerPayload.
        maker_payment_method_id = (
            self.maker_payment_method_id or self.offer_payload.payment_method_id
        )
        taker_payment_method_id = (
            self.taker_payment_method_id or self.offer_payload.payment_method_id
        )
        
        assert maker_payment_method_id, "makerPaymentMethodId must not be null"
        assert taker_payment_method_id, "takerPaymentMethodId must not be null"

        # For SEPA offers we accept also SEPA_INSTANT takers
        # Otherwise both ids need to be the same
        is_valid = (
            maker_payment_method_id == PaymentMethod.SEPA_ID
            and taker_payment_method_id == PaymentMethod.SEPA_INSTANT_ID
        ) or maker_payment_method_id == taker_payment_method_id

        # Note: Original bisq implementation does not assign the validated data back to the object, so we also do not.
        check_argument(
            is_valid,
            f"Payment methods of maker and taker must be the same.\n"
            f"maker_payment_method_id={maker_payment_method_id}\n"
            f"taker_payment_method_id={taker_payment_method_id}"
        )

    @staticmethod
    def from_proto(proto: protobuf.Contract, core_proto_resolver: "CoreProtoResolver"):
        maker_payment_account_payload = core_proto_resolver.from_proto(proto.maker_payment_account_payload) if proto.HasField("maker_payment_account_payload") else None
        taker_payment_account_payload = core_proto_resolver.from_proto(proto.taker_payment_account_payload) if proto.HasField("taker_payment_account_payload") else None
        
        return Contract(
            offer_payload=OfferPayload.from_proto(proto.offer_payload),
            trade_amount=proto.trade_amount,
            trade_price=proto.trade_price,
            taker_fee_tx_id=proto.taker_fee_tx_id,
            buyer_node_address=NodeAddress.from_proto(proto.buyer_node_address),
            seller_node_address=NodeAddress.from_proto(proto.seller_node_address),
            mediator_node_address=NodeAddress.from_proto(proto.mediator_node_address),
            is_buyer_maker_and_seller_taker=proto.is_buyer_maker_and_seller_taker,
            maker_account_id=proto.maker_account_id,
            taker_account_id=proto.taker_account_id,
            maker_payment_account_payload=maker_payment_account_payload,
            taker_payment_account_payload=taker_payment_account_payload,
            maker_pub_key_ring=PubKeyRing.from_proto(proto.maker_pub_key_ring),
            taker_pub_key_ring=PubKeyRing.from_proto(proto.taker_pub_key_ring),
            maker_payout_address_string=proto.maker_payout_address_string,
            taker_payout_address_string=proto.taker_payout_address_string,
            maker_multi_sig_pub_key=proto.maker_multi_sig_pub_key,
            taker_multi_sig_pub_key=proto.taker_multi_sig_pub_key,
            lock_time=proto.lock_time,
            refund_agent_node_address=NodeAddress.from_proto(proto.refund_agent_node_address),
            hash_of_makers_payment_account_payload=ProtoUtil.byte_array_or_none_from_proto(proto.hash_of_makers_payment_account_payload),
            hash_of_takers_payment_account_payload=ProtoUtil.byte_array_or_none_from_proto(proto.hash_of_takers_payment_account_payload),
            maker_payment_method_id=ProtoUtil.string_or_none_from_proto(proto.maker_payment_method_id),
            taker_payment_method_id=ProtoUtil.string_or_none_from_proto(proto.taker_payment_method_id)
        )

    def to_proto_message(self) -> Message:
        message = protobuf.Contract(
            offer_payload=self.offer_payload.to_proto_message().offer_payload,
            trade_amount=self.trade_amount,
            trade_price=self.trade_price,
            taker_fee_tx_id=self.taker_fee_tx_id,
            buyer_node_address=self.buyer_node_address.to_proto_message(),
            seller_node_address=self.seller_node_address.to_proto_message(),
            mediator_node_address=self.mediator_node_address.to_proto_message(),
            is_buyer_maker_and_seller_taker=self.is_buyer_maker_and_seller_taker,
            maker_account_id=self.maker_account_id,
            taker_account_id=self.taker_account_id,
            maker_pub_key_ring=self.maker_pub_key_ring.to_proto_message(),
            taker_pub_key_ring=self.taker_pub_key_ring.to_proto_message(),
            maker_payout_address_string=self.maker_payout_address_string,
            taker_payout_address_string=self.taker_payout_address_string,
            maker_multi_sig_pub_key=self.maker_multi_sig_pub_key,
            taker_multi_sig_pub_key=self.taker_multi_sig_pub_key,
            lock_time=self.lock_time,
        )

        if self.refund_agent_node_address: # bisq/issues/6953 refundAgentNodeAddress sometimes is null
            message.refund_agent_node_address.CopyFrom(self.refund_agent_node_address.to_proto_message())

        if self.hash_of_makers_payment_account_payload:
            message.hash_of_makers_payment_account_payload = self.hash_of_makers_payment_account_payload

        if self.hash_of_takers_payment_account_payload:
            message.hash_of_takers_payment_account_payload = self.hash_of_takers_payment_account_payload

        if self.maker_payment_account_payload:
            message.maker_payment_account_payload.CopyFrom(self.maker_payment_account_payload.to_proto_message())

        if self.taker_payment_account_payload:
            message.taker_payment_account_payload.CopyFrom(self.taker_payment_account_payload.to_proto_message())

        if self.maker_payment_method_id:
            message.maker_payment_method_id = self.maker_payment_method_id

        if self.taker_payment_method_id:
            message.taker_payment_method_id = self.taker_payment_method_id

        return message
    
    @property
    def buyer_payout_address_string(self) -> str:
        return self.maker_payout_address_string if self.is_buyer_maker_and_seller_taker else self.taker_payout_address_string

    @property 
    def seller_payout_address_string(self) -> str:
        return self.taker_payout_address_string if self.is_buyer_maker_and_seller_taker else self.maker_payout_address_string

    @property
    def buyer_pub_key_ring(self) -> "PubKeyRing":
        return self.maker_pub_key_ring if self.is_buyer_maker_and_seller_taker else self.taker_pub_key_ring

    @property
    def seller_pub_key_ring(self) -> "PubKeyRing":
        return self.taker_pub_key_ring if self.is_buyer_maker_and_seller_taker else self.maker_pub_key_ring

    @property
    def buyer_multi_sig_pub_key(self) -> bytes:
        return self.maker_multi_sig_pub_key if self.is_buyer_maker_and_seller_taker else self.taker_multi_sig_pub_key

    @property
    def seller_multi_sig_pub_key(self) -> bytes:
        return self.taker_multi_sig_pub_key if self.is_buyer_maker_and_seller_taker else self.maker_multi_sig_pub_key
    
    @property
    def buyer_payment_account_payload(self) -> Optional[PaymentAccountPayload]:
        return self.maker_payment_account_payload if self.is_buyer_maker_and_seller_taker else self.taker_payment_account_payload

    @property
    def seller_payment_account_payload(self) -> Optional[PaymentAccountPayload]:
        return self.taker_payment_account_payload if self.is_buyer_maker_and_seller_taker else self.maker_payment_account_payload
        

    def set_payment_account_payloads(self, peers_payment_account_payload: PaymentAccountPayload,
                                  my_payment_account_payload: PaymentAccountPayload,
                                  my_pub_key_ring: PubKeyRing):
        if self.is_my_role_maker(my_pub_key_ring):
            self.maker_payment_account_payload = my_payment_account_payload
            self.taker_payment_account_payload = peers_payment_account_payload
        else:
            self.taker_payment_account_payload = my_payment_account_payload
            self.maker_payment_account_payload = peers_payment_account_payload

    def get_hash_of_peers_payment_account_payload(self, my_pub_key_ring: PubKeyRing) -> bytes:
        return self.hash_of_takers_payment_account_payload if self.is_my_role_maker(my_pub_key_ring) else self.hash_of_makers_payment_account_payload

    @property
    def payment_method_id(self) -> str:
        # Either makerPaymentMethodId is set or available in offerPayload
        return self.maker_payment_method_id if self.maker_payment_method_id is not None else \
               OfferPayload(self.offer_payload.get_currency_code()).payment_method_id

    def get_trade_amount(self) -> 'Coin':
        return Coin.value_of(self.trade_amount)

    def get_trade_volume(self) -> 'Volume':
        volume_by_amount = self.get_trade_price().get_volume_by_amount(self.get_trade_amount())
        
        if self.payment_method_id == PaymentMethod.HAL_CASH_ID:
            volume_by_amount = VolumeUtil.get_adjusted_volume_for_hal_cash(volume_by_amount)
        elif is_fiat_currency(self.offer_payload.get_currency_code()):
            volume_by_amount = VolumeUtil.get_rounded_fiat_volume(volume_by_amount)
        
        return volume_by_amount

    def get_trade_price(self) -> Price:
        return Price.value_of(self.offer_payload.get_currency_code(), self.trade_price)

    def get_my_node_address(self, my_pub_key_ring: PubKeyRing) -> NodeAddress:
        if my_pub_key_ring == self.buyer_pub_key_ring:
            return self.buyer_node_address
        else:
            return self.seller_node_address

    def get_peers_node_address(self, my_pub_key_ring: PubKeyRing) -> NodeAddress:
        if my_pub_key_ring == self.seller_pub_key_ring:
            return self.buyer_node_address
        else:
            return self.seller_node_address

    def get_peers_pub_key_ring(self, my_pub_key_ring: PubKeyRing) -> PubKeyRing:
        if my_pub_key_ring == self.seller_pub_key_ring:
            return self.buyer_pub_key_ring
        else:
            return self.seller_pub_key_ring

    def is_my_role_buyer(self, my_pub_key_ring: PubKeyRing) -> bool:
        return self.buyer_pub_key_ring == my_pub_key_ring

    def is_my_role_maker(self, my_pub_key_ring: PubKeyRing) -> bool:
        return self.is_buyer_maker_and_seller_taker == self.is_my_role_buyer(my_pub_key_ring)

    def maybe_clear_sensitive_data(self) -> bool:
        changed = False
        if self.maker_payment_account_payload is not None:
            self.maker_payment_account_payload = None
            changed = True
        if self.taker_payment_account_payload is not None:
            self.taker_payment_account_payload = None
            changed = True
        return changed

    def get_json_dict(self):
        return {
            "offerPayload": self.offer_payload,
            "tradeAmount": self.trade_amount,
            "tradePrice": self.trade_price,
            "takerFeeTxID": self.taker_fee_tx_id,
            "buyerNodeAddress": self.buyer_node_address,
            "sellerNodeAddress": self.seller_node_address,
            "mediatorNodeAddress": self.mediator_node_address,
            "isBuyerMakerAndSellerTaker": self.is_buyer_maker_and_seller_taker,
            "makerAccountId": self.maker_account_id,
            "takerAccountId": self.taker_account_id,
            "makerPaymentAccountPayload": self.maker_payment_account_payload,
            "takerPaymentAccountPayload": self.taker_payment_account_payload,
            "makerPayoutAddressString": self.maker_payout_address_string,
            "takerPayoutAddressString": self.taker_payout_address_string,
            "lockTime": self.lock_time,
            "refundAgentNodeAddress": self.refund_agent_node_address,
            "hashOfMakersPaymentAccountPayload": self.hash_of_makers_payment_account_payload,
            "hashOfTakersPaymentAccountPayload": self.hash_of_takers_payment_account_payload,
            "makerPaymentMethodId": self.maker_payment_method_id,
            "takerPaymentMethodId": self.taker_payment_method_id
        }
        
    @staticmethod
    def sanitize_contract_as_json(contract_as_json: str) -> str:
        """Edits a contract json string, removing the payment account payloads"""
        
        contract_as_json = re.sub(
            r'"takerPaymentAccountPayload":\s*\{[^}]*\}',
            '"takerPaymentAccountPayload": null',
            contract_as_json,
            flags = re.MULTILINE
        )
        contract_as_json = re.sub(
            r'"makerPaymentAccountPayload":\s*\{[^}]*\}',
            '"makerPaymentAccountPayload": null',
            contract_as_json,
            flags = re.MULTILINE
        )
        return contract_as_json

    def print_diff(self, peers_contract_as_json: Optional[str]) -> None:
        if not peers_contract_as_json:
            return

        my_json = JsonUtil.object_to_json(self)
        diff = string_difference(my_json, peers_contract_as_json)
        if diff:
            self.logger.warning(f"Diff of both contracts: \n{diff}")
            self.logger.warning(
                    "\n\n------------------------------------------------------------\n"
                    "Contract as json\n"
                    f"{my_json}"
                    "\n------------------------------------------------------------\n"
                )
            self.logger.warning(
                    "\n\n------------------------------------------------------------\n"
                    "Peers contract as json\n"
                    f"{peers_contract_as_json}"
                    "\n------------------------------------------------------------\n"
                )
        else:
            self.logger.debug("Both contracts are the same")
        
    def __str__(self) -> str:
        return (
            "Contract{"
            f"\n     offer_payload={self.offer_payload}"
            f",\n     trade_amount={self.trade_amount}"
            f",\n     trade_price={self.trade_price}"
            f",\n     taker_fee_tx_id='{self.taker_fee_tx_id}'"
            f",\n     buyer_node_address={self.buyer_node_address}"
            f",\n     seller_node_address={self.seller_node_address}"
            f",\n     mediator_node_address={self.mediator_node_address}"
            f",\n     refund_agent_node_address={self.refund_agent_node_address}"
            f",\n     is_buyer_maker_and_seller_taker={self.is_buyer_maker_and_seller_taker}"
            f",\n     maker_account_id='{self.maker_account_id}'"
            f",\n     taker_account_id='{self.taker_account_id}'"
            f",\n     maker_pub_key_ring={self.maker_pub_key_ring}"
            f",\n     taker_pub_key_ring={self.taker_pub_key_ring}"
            f",\n     maker_payout_address_string='{self.maker_payout_address_string}'"
            f",\n     taker_payout_address_string='{self.taker_payout_address_string}'"
            f",\n     maker_multi_sig_pub_key={bytes_as_hex_string(self.maker_multi_sig_pub_key)}"
            f",\n     taker_multi_sig_pub_key={bytes_as_hex_string(self.taker_multi_sig_pub_key)}"
            f",\n     buyer_multi_sig_pub_key={bytes_as_hex_string(self.buyer_multi_sig_pub_key)}"
            f",\n     seller_multi_sig_pub_key={bytes_as_hex_string(self.seller_multi_sig_pub_key)}"
            f",\n     lock_time={self.lock_time}"
            f",\n     hash_of_makers_payment_account_payload={bytes_as_hex_string(self.hash_of_makers_payment_account_payload)}"
            f",\n     hash_of_takers_payment_account_payload={bytes_as_hex_string(self.hash_of_takers_payment_account_payload)}"
            f",\n     maker_payment_method_id={self.maker_payment_method_id}"
            f",\n     taker_payment_method_id={self.taker_payment_method_id}"
            "\n}"
        )
