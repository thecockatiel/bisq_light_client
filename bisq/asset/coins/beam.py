from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


"""
from original bisq:

Here is info from a Beam developer regarding validation.

Well, unfortunately the range length is quite large. The BbsChannel is 64 bit = 8 bytes, the pubkey is 32 bytes.
So, the length may be up to 80 chars. The minimum length "theoretically" can also drop to a small length, if the
channel==0, and the pubkey starts with many zeroes  (very unlikely, but possible). So, besides being up to 80 chars
lower-case hex there's not much can be tested. A more robust test would also check if the pubkey is indeed valid,
but it's a more complex test, requiring cryptographic code.
"""

@alt_coin_account_disclaimer("account.altcoin.popup.beam.msg")
class Beam(Coin):
    def __init__(self):
        super().__init__(
            name="Beam",
            ticker_symbol="BEAM",
            address_validator=RegexAddressValidator("^([0-9a-f]{1,80})$"),
        )
