from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class SetTxFeeRateOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_TX_FEE_RATE}",
            help="tx fee rate preference (sats/byte)",
            dest=OptLabel.OPT_TX_FEE_RATE,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_TX_FEE_RATE, None):
            raise IllegalArgumentException("no tx fee rate specified")

        return self

    def get_fee_rate(self) -> str:
        return self.options.get(OptLabel.OPT_TX_FEE_RATE, "")
