from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.qwertycoin.msg")
class Qwertycoin(Coin):

    def __init__(self):
        super().__init__(
            name="Qwertycoin",
            ticker_symbol="QWC",
            address_validator=CryptoNoteAddressValidator(validate_checksum=False, valid_prefixes=[0x14820c]),
        )
