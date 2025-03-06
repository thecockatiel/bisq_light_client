from typing import TYPE_CHECKING, Optional
from bisq.common.config.config import Config
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bitcoinj.script.script_type import ScriptType
import pb_pb2 as protobuf
from utils.formatting import get_short_id

if TYPE_CHECKING:
    from bitcoinj.crypto.deterministic_key import DeterministicKey

logger = get_logger(__name__)

# Every trade uses a addressEntry with a dedicated address for all transactions related to the trade.
# That way we have a kind of separated trade wallet, isolated from other transactions and avoiding coin merge.
# If we would not avoid coin merge the user would lose privacy between trades.
class AddressEntry(PersistablePayload):

    # keyPair can be null in case the object is created from deserialization as it is transient.
    # It will be restored when the wallet is ready at setDeterministicKey
    # So after startup it must never be null

    def __init__(self,
                 key_pair: "DeterministicKey" = None, 
                 context: "AddressEntryContext" = None,
                 offer_id: Optional[str] = None,
                 coin_locked_in_multi_sig: int = 0,
                 segwit: bool = False,
                 pub_key: bytes = None,
                 pub_key_hash: bytes = None):
        
        if not key_pair and not (pub_key and pub_key_hash):
            raise ValueError("Either key_pair or pub_key and pub_key_hash must be provided.")
        
        if pub_key and pub_key_hash:
            self.pub_key = pub_key
            self.pub_key_hash = pub_key_hash
        else:
            self.pub_key = key_pair.get_pub_key()
            self.pub_key_hash = key_pair.get_pub_key_hash()

        self.offer_id = offer_id
        self.context = context
        self.coin_locked_in_multi_sig = coin_locked_in_multi_sig
        self.segwit = segwit
        
        # Not an immutable field. Set at startup once wallet is ready and at encrypting/decrypting wallet.
        self.key_pair: Optional["DeterministicKey"] = key_pair # transient
        
        # Only used as cache
        self._address: Optional["Address"] = None # transient
        # Only used as cache
        self._address_string: Optional["str"] = None # transient
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def from_proto(proto: protobuf.AddressEntry) -> "AddressEntry":
        return AddressEntry(
            context=AddressEntryContext.from_proto(proto.context),
            offer_id=ProtoUtil.string_or_none_from_proto(proto.offer_id),
            coin_locked_in_multi_sig=proto.coin_locked_in_multi_sig,
            segwit=proto.segwit,
            pub_key=proto.pub_key,
            pub_key_hash=proto.pub_key_hash,
        )
        
    def to_proto_message(self):
        builder = protobuf.AddressEntry(
            pub_key=self.pub_key,
            pub_key_hash=self.pub_key_hash,
            context=AddressEntryContext.to_proto_message(self.context),
            coin_locked_in_multi_sig=self.coin_locked_in_multi_sig,
            segwit=self.segwit,
        )
        if self.offer_id:
            builder.offer_id = self.offer_id
        return builder
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Set after wallet is ready
    def set_deterministic_key(self, deterministic_key: "DeterministicKey") -> None:
        self.key_pair = deterministic_key

    # get_key_pair must not be called before wallet is ready (in case we get the object recreated from disk deserialization)
    # If the object is created at runtime it must be always constructed after wallet is ready.
    def get_key_pair(self) -> "DeterministicKey":
        assert self.key_pair is not None, "keyPair must not be null. If we got the addressEntry created from PB we need to have " \
                                          "setDeterministicKey got called before any access with getKeyPair()."
        return self.key_pair

    # For display we usually only display the first 8 characters.
    def get_short_offer_id(self) -> Optional[str]:
        return get_short_id(self.offer_id) if self.offer_id else None

    def get_address_string(self) -> Optional[str]:
        if self._address_string is None and self.get_address() is not None:
            self._address_string = str(self.get_address())
        return self._address_string

    def get_address(self) -> Optional["Address"]:
        if self._address is None and self.key_pair is not None:
            script_type = ScriptType.P2WPKH if self.segwit else ScriptType.P2PKH
            self._address = Address.from_key(self.key_pair, script_type, Config.BASE_CURRENCY_NETWORK_VALUE.parameters)
        if self._address is None:
            logger.warning(f"Address is null at getAddress(). keyPair={self.key_pair}")
        return self._address

    @property
    def is_address_null(self) -> bool:
        return self._address is None

    @property
    def is_open_offer(self) -> bool:
        return self.context == AddressEntryContext.OFFER_FUNDING or self.context == AddressEntryContext.RESERVED_FOR_TRADE

    @property
    def is_trade(self) -> bool:
        return self.context == AddressEntryContext.MULTI_SIG or self.context == AddressEntryContext.TRADE_PAYOUT

    def get_coin_locked_in_multi_sig_as_coin(self) -> "Coin":
        return Coin.value_of(self.coin_locked_in_multi_sig)

    def __str__(self) -> str:
        return (f"AddressEntry(address={self.get_address()}, "
                f"context={self.context}, "
                f"offerId='{self.offer_id}', "
                f"coinLockedInMultiSig={self.coin_locked_in_multi_sig}, "
                f"segwit={self.segwit})")


