from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator

@alt_coin_account_disclaimer(message="account.altcoin.popup.arq.msg")
class Arqma(Coin):
    
    def __init__(self):
        super().__init__(
            name="Arqma",
            ticker_symbol="ARQ",
            address_validator=CryptoNoteAddressValidator(valid_prefixes=[0x2cca, 0x6847]),
        )
