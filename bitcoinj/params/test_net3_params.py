from bitcoinj.params.main_net_params import MainNetParams


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
        self.port = 18333
