from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.solo.msg")
class Solo(Coin):

    def __init__(self):
        super().__init__(
            name="Solo",
            ticker_symbol="XSL",
            address_validator=CryptoNoteAddressValidator(valid_prefixes=[13975, 23578]),
        )
