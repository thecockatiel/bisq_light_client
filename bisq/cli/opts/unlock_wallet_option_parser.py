from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from pathlib import Path


class UnlockWalletOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_WALLET_PASSWORD}",
            help="bisq wallet password",
            dest=OptLabel.OPT_WALLET_PASSWORD,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_TIMEOUT}",
            help="wallet unlock timeout (s)",
            dest=OptLabel.OPT_TIMEOUT,
            type=int,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_WALLET_PASSWORD, None):
            raise IllegalArgumentException("no password specified")

        if (
            not self.options.get(OptLabel.OPT_TIMEOUT, None)
            or self.options.get(OptLabel.OPT_TIMEOUT) <= 0
        ):
            raise IllegalArgumentException("no unlock timeout specified")

        return self

    def get_password(self) -> str:
        return self.options.get(OptLabel.OPT_WALLET_PASSWORD)

    def get_unlock_timeout(self) -> int:
        return self.options.get(OptLabel.OPT_TIMEOUT)
