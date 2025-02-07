from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class GetPaymentAccountFormOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_PAYMENT_METHOD_ID}",
            help="id of payment method type used by a payment account",
            dest=OptLabel.OPT_PAYMENT_METHOD_ID,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_PAYMENT_METHOD_ID, None):
            raise IllegalArgumentException("no payment method id specified")

        return self

    def get_payment_method_id(self) -> str:
        return self.options.get(OptLabel.OPT_PAYMENT_METHOD_ID)
