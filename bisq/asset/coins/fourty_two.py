
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator

class FourtyTwo(Coin):
    
    def __init__(self):
        super().__init__(
            name="FourtyTwo",
            ticker_symbol="FRTY",
            address_validator=CryptoNoteAddressValidator(valid_prefixes=[0x1cbd67, 0x13271817]),
        )
        