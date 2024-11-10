
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator

class Aeon(Coin):
    
    def __init__(self):
        super().__init__(
            name="Aeon",
            ticker_symbol="AEON",
            address_validator=CryptoNoteAddressValidator(valid_prefixes=[0xB2, 0x06B8]),
        )
        