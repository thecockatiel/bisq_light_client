from collections import defaultdict
from typing import Any
from bisq.cli.opts.method_otps import MethodOps
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from utils.argparse_ext import CustomArgumentParser


class SimpleMethodOptionParser(MethodOps):

    def __init__(self, args: list[str]):
        self.args = args
        self.parser = CustomArgumentParser(
            allow_abbrev=False,
            add_help=False,
        )
        self.parser.add_argument(
            "-h",
            "--help",
            help="Print method help",
            dest="helpRequested",
            action="store_true",
        )
        self.options = defaultdict[str, Any](lambda: None)
        self.non_option_args: list[str] = []

    def _update_options(self, namespace: Any):
        self.options.update(
            {key: value for key, value in vars(namespace).items() if value is not None}
        )

    def parse(self):
        try:
            ns, non_args = self.parser.parse_known_args(self.args)
            self._update_options(ns)
            self.non_option_args = non_args
            return self
        except Exception as e:
            raise IllegalArgumentException(SimpleMethodOptionParser._cli_exception_message_style(e), e)
        
    def is_for_help(self) -> bool:
        return self.options.get("helpRequested", False)
    
    def verify_string_is_valid_decimal(self, string: str):
        try:
            float(string)
        except:
            raise IllegalArgumentException(f"{string} is not a number")
        
    def value_not_specified(self, opt: str) -> bool:
        return self.options.get(opt, None) is None or self.options.get(opt, None) == ""
        
    def _cli_exception_message_style(self, ex: Exception) -> str:
        message = str(ex)
        if not message:
            return None

        option_token = "option "
        cli_message = message.lower()
        if cli_message.startswith(option_token) and len(cli_message) > len(option_token):
            cli_message = cli_message[cli_message.index(" ") + 1:]
        return cli_message