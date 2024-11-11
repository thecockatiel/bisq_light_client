from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator


class Mask(Coin):

    def __init__(self):
        super().__init__(
            name="Mask",
            ticker_symbol="MASK",
            address_validator=CryptoNoteAddressValidator(valid_prefixes=[123, 206]),
        )
