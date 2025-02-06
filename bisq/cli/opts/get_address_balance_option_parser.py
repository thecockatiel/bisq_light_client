from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class GetAddressBalanceOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_ADDRESS}",
            help="wallet btc address",
            dest=OptLabel.OPT_ADDRESS,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        address = self.options.get(OptLabel.OPT_ADDRESS, None)
        if not address:
            raise IllegalArgumentException("no address specified")

        return self

    def get_address(self) -> str:
        return self.options.get(OptLabel.OPT_ADDRESS)
