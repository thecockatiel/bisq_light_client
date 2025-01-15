from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.monetary_format import MonetaryFormat
from bitcoinj.core.network_parameters import NetworkParameters


from typing import Any


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
        self.port = 8333

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