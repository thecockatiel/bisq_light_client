from abc import ABC
from datetime import timedelta
import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Dict

from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload
from bisq.core.network.p2p.storage.payload.requires_owner_is_online_payload import RequiresOwnerIsOnlinePayload

if TYPE_CHECKING:
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.offer.offer_direction import OfferDirection

@dataclass(kw_only=True)
class OfferPayloadBase(
    ProtectedStoragePayload, ExpirablePayload, RequiresOwnerIsOnlinePayload, ABC
):
    TTL: int = field(default=int(timedelta(minutes=9).total_seconds() * 1000), init=False)

    id: str
    date: int
    # For fiat offer the baseCurrencyCode is BTC and the counterCurrencyCode is the fiat currency
    # For altcoin offers it is the opposite. baseCurrencyCode is the altcoin and the counterCurrencyCode is BTC.
    base_currency_code: str
    counter_currency_code: str
    # price if fixed price is used (usePercentageBasedPrice = false), otherwise 0
    price: int
    amount: int
    min_amount: int
    payment_method_id: str
    maker_payment_account_id: str
    owner_node_address: "NodeAddress"
    direction: "OfferDirection"
    version_nr: str
    protocol_version: int
    pub_key_ring: "PubKeyRing"
    # cache
    hash: Optional[bytes] = field(default=None, repr=False, hash=False)
    extra_data_map: Optional[Dict[str, str]] = field(default=None)

    def get_hash(self):
        if self.hash is None:
            self.hash = hashlib.sha256(self.serialize_for_hash()).digest()
        return self.hash
    
    def __hash__(self) -> int:
        return hash(self.get_hash())
        

    def get_owner_pub_key(self):
        return self.pub_key_ring.signature_pub_key

    # In the offer we support base and counter currency
    # Fiat offers have base currency BTC and counterCurrency Fiat
    # Altcoins have base currency Altcoin and counterCurrency BTC
    # The rest of the app does not support yet that concept of base currency and counter currencies
    # so we map here for convenience
    def get_currency_code(self):
        return (
            self.counter_currency_code
            if self.base_currency_code == "BTC"
            else self.base_currency_code
        )

    def get_ttl(self):
        return self.TTL
    
    def get_owner_node_address(self):
        return self.owner_node_address

    def __str__(self) -> str:
        return (
            f"OfferPayloadBase{{\n"
            f"     id='{self.id}',\n"
            f"     date={self.date},\n"
            f"     base_currency_code='{self.base_currency_code}',\n"
            f"     counter_currency_code='{self.counter_currency_code}',\n"
            f"     price={self.price},\n"
            f"     amount={self.amount},\n"
            f"     min_amount={self.min_amount},\n"
            f"     payment_method_id='{self.payment_method_id}',\n"
            f"     maker_payment_account_id='{self.maker_payment_account_id}',\n"
            f"     owner_node_address={self.owner_node_address},\n"
            f"     direction={self.direction},\n"
            f"     version_nr='{self.version_nr}',\n"
            f"     protocol_version={self.protocol_version},\n"
            f"     pub_key_ring={self.pub_key_ring},\n"
            f"     hash={'null' if self.hash is None else self.hash.hex()},\n"
            f"     extra_data_map={self.extra_data_map}\n"
            f"}}"
        )

    def serialize_for_hash(self) -> bytes:
        return super().serialize_for_hash()
