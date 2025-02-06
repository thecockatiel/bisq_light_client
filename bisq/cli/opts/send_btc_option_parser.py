from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class SendBtcOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_ADDRESS}",
            help="destination bsq address",
            dest=OptLabel.OPT_ADDRESS,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_AMOUNT}",
            help="amount of bsq to send",
            dest=OptLabel.OPT_AMOUNT,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_TX_FEE_RATE}",
            help="optional tx fee rate (sats/byte)",
            dest=OptLabel.OPT_TX_FEE_RATE,
            type=str,
            default="",
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_MEMO}",
            help="optional tx memo",
            dest=OptLabel.OPT_MEMO,
            type=str,
            default="",
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_ADDRESS, None):
            raise IllegalArgumentException("no btc address specified")

        if not self.options.get(OptLabel.OPT_AMOUNT, None):
            raise IllegalArgumentException("no btc amount specified")

        return self

    def get_address(self) -> str:
        return self.options.get(OptLabel.OPT_ADDRESS)

    def get_amount(self) -> str:
        return self.options.get(OptLabel.OPT_AMOUNT)

    def get_fee_rate(self) -> str:
        return self.options.get(OptLabel.OPT_TX_FEE_RATE, "")

    def get_memo(self) -> str:
        return self.options.get(OptLabel.OPT_MEMO, "")
