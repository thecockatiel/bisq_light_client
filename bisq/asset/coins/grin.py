from bisq.asset.alt_coin_account_disclaimer import alt_coin_account_disclaimer
from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bisq.asset.coin import Coin
from electrum_min.segwit_addr import bech32_decode


class GrinAddressValidator(AddressValidator):
    def validate(self, address: str):
        try:
            bech_data = bech32_decode(address)
            if bech_data.hrp != "grin":
                return AddressValidationResult.invalid_address(
                    f"invalid address prefix: {bech_data.hrp}"
                )
            if len(bech_data.data) != 52:
                 return AddressValidationResult.invalid_address(
                    f"invalid address length: {len(bech_data.hrp)}"
                )
            return AddressValidationResult.valid_address()
        except:
            return AddressValidationResult.invalid_structure()
        


@alt_coin_account_disclaimer("account.altcoin.popup.grin.msg")
class Grin(Coin):

    def __init__(self):
        super().__init__(
            name="Grin",
            ticker_symbol="GRIN",
            address_validator=GrinAddressValidator(),
        )
