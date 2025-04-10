class CurrencyTuple:
    def __init__(
        self,
        code: str,
        name: str,
        precision: int = 4,
    ):

        self.code = code
        self.name = name
        # precision 4 is 1/10000 -> 0.0001 is smallest unit
        # We use Fiat class and the precision is 4
        self.precision = precision

    def __str__(self):
        return f"CurrencyTuple(code={self.code}, name={self.name}, precision={self.precision})"

    def __eq__(self, other):
        if isinstance(other, CurrencyTuple):
            return (
                self.code == other.code
                and self.name == other.name
                and self.precision == other.precision
            )
        return False

    def __hash__(self):
        return hash((self.code, self.name, self.precision))
