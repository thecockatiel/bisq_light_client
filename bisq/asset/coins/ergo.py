from bisq.asset.address_validation_result import AddressValidationResult
from bisq.asset.address_validator import AddressValidator
from bisq.asset.coin import Coin
from bisq.asset.network_parameters_adapter import NetworkParametersAdapter
from electrum_min.bitcoin import base_decode
from electrum_min.util import to_bytes


class ErgoAddressValidator(AddressValidator):

    def validate(self, address: str):
        try:
            address = to_bytes(address, 'ascii')
            decoded = base_decode(address, base=58)
            if len(decoded) < 4:
                return AddressValidationResult.invalid_address(f"Input too short: {len(decoded)}")
            if decoded[0] != 1 and decoded[0] != 2 and decoded[0] != 3:
                return AddressValidationResult.invalid_address("Invalid prefix")
        except Exception as e:
            return AddressValidationResult.invalid_address(str(e))
        return AddressValidationResult.valid_address()


class Ergo(Coin):

    def __init__(self):
        super().__init__(
            name="Ergo",
            ticker_symbol="ERG",
            address_validator=ErgoAddressValidator(),
        )
