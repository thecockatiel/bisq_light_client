from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.msr.msg")
class Masari(Coin):

    def __init__(self):
        super().__init__(
            name="Masari",
            ticker_symbol="MSR",
            address_validator=CryptoNoteAddressValidator(valid_prefixes=[28, 52]),
        )
