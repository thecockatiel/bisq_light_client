from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from pathlib import Path


class CreatePaymentAccountOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_PAYMENT_ACCOUNT_FORM}",
            help="path to json payment account form",
            dest=OptLabel.OPT_PAYMENT_ACCOUNT_FORM,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_FORM, None):
            raise IllegalArgumentException(
                "no path to json payment account form specified"
            )

        payment_acct_form_path = Path(
            self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_FORM)
        )
        if not payment_acct_form_path.exists():
            raise IllegalArgumentException(
                f"json payment account form '{payment_acct_form_path}' could not be found"
            )

        return self

    def get_payment_account_form(self) -> Path:
        return Path(self.options.get(OptLabel.OPT_PAYMENT_ACCOUNT_FORM))
