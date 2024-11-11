from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.bitcoin_address_validator import BitcoinAddressValidator
from bisq.asset.coin import Coin
from bitcoinj.core.network_parameters import MainNetParams, TestNet3Params, RegTestParams, NetworkParameters

class BSQAddressValidator(BitcoinAddressValidator):
    
    def validate(self, address: str):
        if not address.startswith("B"):
            return AddressValidationResult.invalid_address("BSQ address must start with 'B'")
        
        address_at_btc = address[1:]
        
        return super().validate(address_at_btc)

class BSQ(Coin):
    
    def __init__(self, network: Coin.Network, network_parameters: NetworkParameters):
        super().__init__(
            name="BSQ",
            ticker_symbol="BSQ",    
            address_validator=BSQAddressValidator(network_parameters),
            network=network,
        )
    
    Mainnet = lambda: BSQ(Coin.Network.MAINNET, MainNetParams())
    Testnet = lambda: BSQ(Coin.Network.TESTNET, TestNet3Params())
    Regtest = lambda: BSQ(Coin.Network.REGTEST, RegTestParams())
    
