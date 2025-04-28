from typing import Optional
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import parse_bool


class SetUserAliasOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_USER_ID}",
            help="user-id to set alias for",
            dest=OptLabel.OPT_USER_ID,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_ALIAS}",
            help="alias to set on given user-id",
            dest=OptLabel.OPT_ALIAS,
            type=str,
        )
        self.user_id: Optional[str] = None
        self.alias: Optional[str] = None

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        self.user_id = self.options.get(OptLabel.OPT_USER_ID, None)
        self.alias = self.options.get(OptLabel.OPT_ALIAS, None)

        if not self.user_id:
            raise IllegalArgumentException("no user-id specified")

        if not self.alias:
            raise IllegalArgumentException("no alias specified")

        return self
