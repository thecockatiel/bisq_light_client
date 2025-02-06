from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class GetTransactionOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_TRANSACTION_ID}",
            help="id of transaction",
            dest=OptLabel.OPT_TRANSACTION_ID,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_TRANSACTION_ID, None):
            raise IllegalArgumentException("no tx id specified")

        return self

    def get_tx_id(self) -> str:
        return self.options.get(OptLabel.OPT_TRANSACTION_ID)
