from typing import Optional
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from grpc_pb2 import GetTradesRequest


class GetTradesOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parsed_category: Optional[GetTradesRequest.Category] = None
        self.parser.add_argument(
            f"--{OptLabel.OPT_CATEGORY}",
            help="category of trades (open|closed|failed)",
            dest=OptLabel.OPT_CATEGORY,
            type=str,
            choices=["open", "closed", "failed"],
            default="open",
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        category = self.options.get(OptLabel.OPT_CATEGORY)
        if category == "open":
            self.parsed_category = GetTradesRequest.Category.OPEN
        elif category == "closed":
            self.parsed_category = GetTradesRequest.Category.CLOSED
        elif category == "failed":
            self.parsed_category = GetTradesRequest.Category.FAILED
        else:
            raise IllegalArgumentException(f"invalid category: {category}")

        return self

    def get_category(self):
        return self.parsed_category

    def get_category_name(self):
        return self.options.get(OptLabel.OPT_CATEGORY)
