from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.bitcoin_address_validator import BitcoinAddressValidator
from bisq.asset.coin import Coin
from electrum_min.constants import AbstractNet, BitcoinMainnet, BitcoinRegtest, BitcoinTestnet

class BSQAddressValidator(BitcoinAddressValidator):
    
    def validate(self, address: str):
        if not address.startswith("B"):
            return AddressValidationResult.invalid_address("BSQ address must start with 'B'")
        
        address_at_btc = address[1:]
        
        return super().validate(address_at_btc)

class BSQ(Coin):
    
    def __init__(self, network: Coin.Network, net: AbstractNet):
        super().__init__(
            name="BSQ",
            ticker_symbol="BSQ",    
            address_validator=BSQAddressValidator(net),
            network=network,
        )
    
    Mainnet = lambda: BSQ(Coin.Network.MAINNET, BitcoinMainnet())
    Testnet = lambda: BSQ(Coin.Network.TESTNET, BitcoinTestnet())
    Regtest = lambda: BSQ(Coin.Network.REGTEST, BitcoinRegtest())
    
