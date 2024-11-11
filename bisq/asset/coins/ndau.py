from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Ndau(Coin):

    def __init__(self):
        # note: ndau addresses contain an internal checksum which was deemed too complicated to include here.
        # this regex performs superficial validation, but there is a large space of addresses marked valid
        # by this regex which are not in fact valid ndau addresses. For actual ndau address validation,
        # use the Address class in github.com/oneiro-ndev/ndauj (java) or github.com/oneiro-ndev/ndaumath/pkg/address (go).
        super().__init__(
            name="Ndau",
            ticker_symbol="XND",
            address_validator=RegexAddressValidator("^nd[anexbm][abcdefghijkmnpqrstuvwxyz23456789]{45}$"),
        )

