from bisq.cli.currency_format import CurrencyFormat
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class GetTradeOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_TRADE_ID}",
            help="id of trade",
            dest=OptLabel.OPT_TRADE_ID,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_SHOW_CONTRACT}",
            help="show trade's json contract",
            dest=OptLabel.OPT_SHOW_CONTRACT,
            type=parse_bool,
            metavar="<Boolean>",
            nargs="?",
            const=True,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_TX_ID}",
            help="optional tx id",
            dest=OptLabel.OPT_TX_ID,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_TX_KEY}",
            help="optional tx key",
            dest=OptLabel.OPT_TX_KEY,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_TRADE_ID, None):
            raise IllegalArgumentException("no trade id specified")

        return self

    def get_trade_id(self) -> str:
        return self.options.get(OptLabel.OPT_TRADE_ID)

    def get_show_contract(self) -> bool:
        return self.options.get(OptLabel.OPT_SHOW_CONTRACT, False)

    def get_tx_id(self) -> str:
        return self.options.get(OptLabel.OPT_TX_ID, "")

    def get_tx_key(self) -> str:
        return self.options.get(OptLabel.OPT_TX_KEY, "")
