from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.blur.msg")
class Blur(Coin):

    def __init__(self):
        super().__init__(
            name="Blur",
            ticker_symbol="BLUR",
            address_validator=CryptoNoteAddressValidator(
                valid_prefixes=[0x1e4d, 0x2195]
            ),
        )
