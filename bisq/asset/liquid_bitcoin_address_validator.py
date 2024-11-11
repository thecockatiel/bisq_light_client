from bisq.asset.regex_address_validator import RegexAddressValidator


class LiquidBitcoinAddressValidator(RegexAddressValidator):

    def __init__(self):
        super().__init__(
            "^([a-km-zA-HJ-NP-Z1-9]{26,35}|[a-km-zA-HJ-NP-Z1-9]{80}|[a-z]{2,5}1[ac-hj-np-z02-9]{8,87}|[A-Z]{2,5}1[AC-HJ-NP-Z02-9]{8,87})$",
            "validation.altcoin.liquidBitcoin.invalidAddress",
        )
