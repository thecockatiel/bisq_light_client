from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class GetAvgBsqPriceOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_DAYS}",
            help="number of days in average bsq price calculation",
            dest=OptLabel.OPT_DAYS,
            type=int,
            default=30,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        days = self.options.get(OptLabel.OPT_DAYS, None)
        if not days or days <= 0:
            raise IllegalArgumentException("no # of days specified")

        return self

    def get_days(self):
        return self.options.get(OptLabel.OPT_DAYS)
