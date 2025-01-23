from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.monetary_format import MonetaryFormat


# I decided to implement it incomplete because it is a very large class and I am not sure if it is necessary to implement it completely.
# TODO: complete?
class NetworkParameters(ABC):
    PAYMENT_PROTOCOL_ID_MAINNET = "main"
    PAYMENT_PROTOCOL_ID_TESTNET = "test"
    PAYMENT_PROTOCOL_ID_UNIT_TESTS = "unittest"
    PAYMENT_PROTOCOL_ID_REGTEST = "regtest"
    MAX_MONEY = Coin.COIN().multiply(21000000)
    
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
        self.port = -1

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

    @abstractmethod
    def get_payment_protocol_id(self) -> str:
        pass
