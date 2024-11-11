from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.crypto_note_address_validator import CryptoNoteAddressValidator


@alt_coin_account_disclaimer("account.altcoin.popup.pars.msg")
class ParsiCoin(Coin):

    def __init__(self):
        super().__init__(
            name="ParsiCoin",
            ticker_symbol="PARS",
            address_validator=CryptoNoteAddressValidator(validate_checksum=False, valid_prefixes=[0x90004]),
        )
