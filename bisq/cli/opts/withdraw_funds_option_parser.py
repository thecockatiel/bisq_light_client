from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class WithdrawFundsOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_TRADE_ID}",
            help="id of trade",
            dest=OptLabel.OPT_TRADE_ID,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_ADDRESS}",
            help="destination btc address",
            dest=OptLabel.OPT_ADDRESS,
            type=str,
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

        if not self.options.get(OptLabel.OPT_TRADE_ID, None):
            raise IllegalArgumentException("no trade id specified")

        if not self.options.get(OptLabel.OPT_ADDRESS, None):
            raise IllegalArgumentException("no destination address specified")

        return self

    def get_trade_id(self) -> str:
        return self.options.get(OptLabel.OPT_TRADE_ID)

    def get_address(self) -> str:
        return self.options.get(OptLabel.OPT_ADDRESS)

    def get_memo(self) -> str:
        return self.options.get(OptLabel.OPT_MEMO, "")
