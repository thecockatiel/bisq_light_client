from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.monetary_format import MonetaryFormat


# I decided to implement it incomplete because it is a very large class and I am not sure if it is necessary to implement it completely.
# TODO: complete?
class NetworkParameters(ABC):
    class ProtocolVersion(Enum):
        MINIMUM = 70000
        PONG = 60001
        BLOOM_FILTER = 70000  # BIP37
        BLOOM_FILTER_BIP111 = 70011  # BIP111
        WITNESS_VERSION = 70012
        FEEFILTER = 70013  # BIP133
        CURRENT = 70013

        def __init__(self, bitcoin_protocol: int):
            self.bitcoin_protocol = bitcoin_protocol
            
        def __new__(cls, *args, **kwds):
            value = len(cls.__members__)
            obj = object.__new__(cls)
            obj._value_ = value
            return obj

        def get_bitcoin_protocol_version(self) -> int:
            return self.bitcoin_protocol

    #  The string returned by getId() for the main, production network where people trade things.
    ID_MAINNET = "org.bitcoin.production"
    # The string returned by getId() for the testnet.
    ID_TESTNET = "org.bitcoin.test"
    # The string returned by getId() for regtest mode.
    ID_REGTEST = "org.bitcoin.regtest"
    # Unit test network.
    ID_UNITTESTNET = "org.bitcoinj.unittest"

    # The string used by the payment protocol to represent the main net.
    PAYMENT_PROTOCOL_ID_MAINNET = "main"
    # The string used by the payment protocol to represent the test net.
    PAYMENT_PROTOCOL_ID_TESTNET = "test"
    # The string used by the payment protocol to represent unit testing (note that this is non-standard).
    PAYMENT_PROTOCOL_ID_UNIT_TESTS = "unittest"
    PAYMENT_PROTOCOL_ID_REGTEST = "regtest"

    def __init__(self):
        self.address_header: int = 0
        self.p2sh_header: int = 0
        self.segwit_address_hrp: int = 0
        self.id: str = None
        self.bip32_header_P2PKH_pub = None
        self.bip32_header_P2PKH_priv = None
        self.bip32_header_P2WPKH_pub = None
        self.bip32_header_P2WPKH_priv = None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, NetworkParameters):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        return hash(self.id)

    @abstractmethod
    def get_max_money(self) -> Coin:
        """Returns the number of coins that will be produced in total, on this
        network. Where not applicable, a very large number of coins is returned
        instead (i.e. the main coin issue for Dogecoin)."""
        pass

    @abstractmethod
    def get_min_non_dust_output(self) -> Coin:
        """Any standard (ie P2PKH) output smaller than this value will
        most likely be rejected by the network."""
        pass

    @abstractmethod
    def get_monetary_format(self) -> MonetaryFormat:
        """The monetary object for this currency."""
        pass

    @abstractmethod
    def get_uri_scheme(self) -> str:
        """Scheme part for URIs, for example "bitcoin"."""
        pass

    @abstractmethod
    def has_max_money(self) -> bool:
        """Returns whether this network has a maximum number of coins (finite supply) or
        not. Always returns true for Bitcoin, but exists to be overridden for other
        networks."""
        pass

    @abstractmethod
    def get_serializer(self, parse_retain: bool) -> Any:
        """Construct and return a custom serializer."""
        pass

    @abstractmethod
    def get_protocol_version_num(self, version: ProtocolVersion) -> int:
        """Get protocol version number for the given protocol version."""
        pass

class MainNetParams(NetworkParameters):
    def __init__(self):
        super().__init__()
        self.address_header = 0
        self.p2sh_header = 5
        self.segwit_address_hrp = "bc"
        self.id = self.ID_MAINNET
        self.bip32_header_P2PKH_pub = 0x0488b21e; # The 4 byte header that serializes in base58 to "xpub".
        self.bip32_header_P2PKH_priv = 0x0488ade4; # The 4 byte header that serializes in base58 to "xprv"
        self.bip32_header_P2WPKH_pub = 0x04b24746; # The 4 byte header that serializes in base58 to "zpub".
        self.bip32_header_P2WPKH_priv = 0x04b2430c; # The 4 byte header that serializes in base58 to "zprv"

    def get_max_money(self) -> Coin:
        return Coin.COIN().multiply(21000000)

    def get_min_non_dust_output(self) -> Coin:
        return Coin.value_of(546) # satoshis

    def get_monetary_format(self) -> MonetaryFormat:
        return MonetaryFormat.BTC()

    def get_uri_scheme(self) -> str:
        return "bitcoin"

    def has_max_money(self) -> bool:
        return True

    def get_serializer(self, parse_retain: bool) -> Any:
        return None

    def get_protocol_version_num(self, version: NetworkParameters.ProtocolVersion) -> int:
        return version.get_bitcoin_protocol_version()
    
class RegTestParams(MainNetParams):
    def __init__(self):
        super().__init__()
        self.address_header = 111
        self.p2sh_header = 196
        self.segwit_address_hrp = "bcrt"
        self.id = self.ID_REGTEST
        self.bip32_header_P2PKH_pub = 0x043587cf # The 4 byte header that serializes in base58 to "tpub".
        self.bip32_header_P2PKH_priv = 0x04358394 # The 4 byte header that serializes in base58 to "tprv"
        self.bip32_header_P2WPKH_pub = 0x045f1cf6 # The 4 byte header that serializes in base58 to "vpub".
        self.bip32_header_P2WPKH_priv = 0x045f18bc # The 4 byte header that serializes in base58 to "vprv"

class TestNet3Params(MainNetParams):
    def __init__(self):
        super().__init__()
        self.address_header = 111
        self.p2sh_header = 196
        self.segwit_address_hrp = "tb"
        self.id = self.ID_TESTNET
        self.bip32_header_P2PKH_pub = 0x043587cf # The 4 byte header that serializes in base58 to "tpub".
        self.bip32_header_P2PKH_priv = 0x04358394 # The 4 byte header that serializes in base58 to "tprv"
        self.bip32_header_P2WPKH_pub = 0x045f1cf6 # The 4 byte header that serializes in base58 to "vpub".
        self.bip32_header_P2WPKH_priv = 0x045f18bc # The 4 byte header that serializes in base58 to "vprv"

class UnitTestParams(MainNetParams):
    def __init__(self):
        super().__init__()
        self.address_header = 111
        self.p2sh_header = 196
        self.segwit_address_hrp = "tb"
        self.id = self.ID_UNITTESTNET
        self.bip32_header_P2PKH_pub = 0x043587cf # The 4 byte header that serializes in base58 to "tpub".
        self.bip32_header_P2PKH_priv = 0x04358394 # The 4 byte header that serializes in base58 to "tprv"
        self.bip32_header_P2WPKH_pub = 0x045f1cf6 # The 4 byte header that serializes in base58 to "vpub".
        self.bip32_header_P2WPKH_priv = 0x045f18bc # The 4 byte header that serializes in base58 to "vprv"