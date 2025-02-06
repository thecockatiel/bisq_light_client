from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class CreateOfferOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_PAYMENT_ACCOUNT_ID}",
            help="id of payment account used for offer",
            dest=OptLabel.OPT_PAYMENT_ACCOUNT_ID,
            type=str,
            default="",
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_DIRECTION}",
            help="offer direction (buy|sell)",
            dest=OptLabel.OPT_DIRECTION,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_CURRENCY_CODE}",
            help="currency code (bsq|xmr|eur|usd|...)",
            dest=OptLabel.OPT_CURRENCY_CODE,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_AMOUNT}",
            help="amount of btc to buy or sell",
            dest=OptLabel.OPT_AMOUNT,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_MIN_AMOUNT}",
            help="minimum amount of btc to buy or sell",
            dest=OptLabel.OPT_MIN_AMOUNT,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_MKT_PRICE_MARGIN}",
            help="market btc price margin (%)",
            dest=OptLabel.OPT_MKT_PRICE_MARGIN,
            type=str,
            default="0.00",
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_FIXED_PRICE}",
            help="fixed btc price",
            dest=OptLabel.OPT_FIXED_PRICE,
            type=str,
            default="0",
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_SECURITY_DEPOSIT}",
            help="maker security deposit (%)",
            dest=OptLabel.OPT_SECURITY_DEPOSIT,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_FEE_CURRENCY}",
            help="maker fee currency code (bsq|btc)",
            dest=OptLabel.OPT_FEE_CURRENCY,
            type=str,
            default="btc",
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_SWAP}",
            help="create bsq swap offer",
            dest=OptLabel.OPT_SWAP,
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_DIRECTION, None):
            raise IllegalArgumentException("no direction (buy|sell) specified")

        if not self.options.get(OptLabel.OPT_CURRENCY_CODE, None):
            raise IllegalArgumentException("no currency code specified")

        if not self.options.get(OptLabel.OPT_AMOUNT, None):
            raise IllegalArgumentException("no btc amount specified")

        if self.get_is_swap():
            if (
                not str(self.options.get(OptLabel.OPT_CURRENCY_CODE, None)).lower()
                == "bsq"
            ):
                raise IllegalArgumentException("only bsq swaps are currently supported")

            if self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_ID, None):
                raise IllegalArgumentException(
                    "cannot use a payment account id in bsq swap offer"
                )

            if self.options.get(OptLabel.OPT_MKT_PRICE_MARGIN, None):
                raise IllegalArgumentException(
                    "cannot use a market price margin in bsq swap offer"
                )

            if self.options.get(OptLabel.OPT_SECURITY_DEPOSIT, None):
                raise IllegalArgumentException(
                    "cannot use a security deposit in bsq swap offer"
                )

            if not self.options.get(OptLabel.OPT_FIXED_PRICE, None):
                raise IllegalArgumentException("no fixed price specified")
        else:
            if not self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_ID, None):
                raise IllegalArgumentException("no payment account id specified")

            if not self.options.get(
                OptLabel.OPT_MKT_PRICE_MARGIN, None
            ) and not self.options.get(OptLabel.OPT_FIXED_PRICE, None):
                raise IllegalArgumentException(
                    "no market price margin or fixed price specified"
                )

            if OptLabel.OPT_MKT_PRICE_MARGIN in self.options:
                mkt_price_margin_pct_string = self.options.get(
                    OptLabel.OPT_MKT_PRICE_MARGIN
                )
                if not mkt_price_margin_pct_string:
                    raise IllegalArgumentException("no market price margin specified")
                else:
                    self.verify_string_is_valid_decimal(mkt_price_margin_pct_string)

            if OptLabel.OPT_FIXED_PRICE in self.options and not self.options.get(
                OptLabel.OPT_FIXED_PRICE
            ):
                raise IllegalArgumentException("no fixed price specified")

            if not self.options.get(OptLabel.OPT_SECURITY_DEPOSIT, None):
                raise IllegalArgumentException("no security deposit specified")
            else:
                self.verify_string_is_valid_decimal(
                    self.options.get(OptLabel.OPT_SECURITY_DEPOSIT)
                )

        return self

    def get_payment_account_id(self) -> str:
        return self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_ID, "")

    def get_direction(self) -> str:
        return self.options.get(OptLabel.OPT_DIRECTION, "")

    def get_currency_code(self) -> str:
        return self.options.get(OptLabel.OPT_CURRENCY_CODE, "")

    def get_amount(self) -> str:
        return self.options.get(OptLabel.OPT_AMOUNT, "")

    def get_min_amount(self) -> str:
        return self.options.get(OptLabel.OPT_MIN_AMOUNT, "") or self.get_amount()

    def is_using_mkt_price_margin(self) -> bool:
        opt = self.options.get(OptLabel.OPT_MKT_PRICE_MARGIN, "")
        return opt and opt != "0.00"

    def get_mkt_price_margin_pct(self) -> float:
        return float(self.options.get(OptLabel.OPT_MKT_PRICE_MARGIN, "") or "0.00")

    def get_fixed_price(self) -> str:
        return self.options.get(OptLabel.OPT_FIXED_PRICE, "") or "0.00"

    def get_security_deposit_pct(self) -> float:
        return float(self.options.get(OptLabel.OPT_SECURITY_DEPOSIT, ""))

    def get_maker_fee_currency_code(self) -> str:
        return self.options.get(OptLabel.OPT_FEE_CURRENCY, "") or "btc"

    def get_is_swap(self) -> bool:
        return self.options.get(OptLabel.OPT_SWAP, "") or False
