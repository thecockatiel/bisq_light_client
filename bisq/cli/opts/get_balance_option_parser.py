from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser


class GetBalanceOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_CURRENCY_CODE}",
            help="wallet currency code (bsq|btc)",
            dest=OptLabel.OPT_CURRENCY_CODE,
            type=str,
            default="",
        )

    def get_currency_code(self) -> str:
        return self.options.get(OptLabel.OPT_CURRENCY_CODE, "")
