from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class RegisterDisputeAgentOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_DISPUTE_AGENT_TYPE}",
            help="dispute agent type",
            dest=OptLabel.OPT_DISPUTE_AGENT_TYPE,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_REGISTRATION_KEY}",
            help="registration key",
            dest=OptLabel.OPT_REGISTRATION_KEY,
            type=str,
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_DISPUTE_AGENT_TYPE, None):
            raise IllegalArgumentException("no dispute agent type specified")

        if not self.options.get(OptLabel.OPT_REGISTRATION_KEY, None):
            raise IllegalArgumentException("no registration key specified")

        return self

    def get_dispute_agent_type(self) -> str:
        return self.options.get(OptLabel.OPT_DISPUTE_AGENT_TYPE)

    def get_registration_key(self) -> str:
        return self.options.get(OptLabel.OPT_REGISTRATION_KEY)
