from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class GetBTCMarketPriceOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_CURRENCY_CODE}",
            help="currency-code",
            dest=OptLabel.OPT_CURRENCY_CODE,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        code = self.options.get(OptLabel.OPT_CURRENCY_CODE, None)
        if not code:
            raise IllegalArgumentException("no currency code specified")

        return self

    def get_currency_code(self):
        return self.options.get(OptLabel.OPT_CURRENCY_CODE)
