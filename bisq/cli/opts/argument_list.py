from typing import Iterable


class ArgumentList:
    """
    Wrapper for an array of command line arguments.

    Used to extract CLI connection and authentication arguments, or method arguments
    before parsing CLI or method opts
    """

    def __init__(self, arguments: Iterable[str]):
        self._arguments = list[str](arguments)
        self._index = 0

    def is_cli_opt(self, argument: str):
        return argument.startswith(
            ("--password", "-password", "--port", "-port", "--host", "-host")
        )

    def get_arguments(self):
        """
        Returns only the CLI connection & authentication, and method name args
        (--password, --host, --port, --help, method name) contained in the original
        list of arguments; excludes the method specific arguments.

        If the list of arguments contains both a method name (the only positional opt)
        and a help argument (--help, -help), it is assumed the user wants method help,
        not CLI help, and the help argument is not included in the returned list.
        """

        self._index = 0
        method_name_argument = None
        help_argument = None
        cli_arguments = []
        method_arguments = []

        while self.has_more():
            arg = self.peek()
            if not method_name_argument and self.is_method_name_opt(arg):
                method_name_argument = arg
                cli_arguments.append(arg)
            elif self.is_cli_opt(arg):
                cli_arguments.append(arg)
            elif self.is_help_opt(arg):
                help_argument = arg
            else:
                method_arguments.append(arg)

            self.next()

        if help_argument is not None:
            if method_name_argument is None:
                cli_arguments.append(help_argument)
            else:
                method_arguments.append(help_argument)

        return cli_arguments, method_arguments

    # The method name is the only positional opt in a command (easy to identify).
    # If the positional argument does not match a Method, or there are more than one
    # positional arguments, the joptsimple parser or CLI will fail as expected.
    def is_method_name_opt(self, argument: str):
        return not argument.startswith("-")

    def is_help_opt(self, argument: str):
        return argument.startswith(("--help", "-help")) or argument == "-h"

    def has_more(self):
        return self._index < len(self._arguments)

    def next(self):
        result = self._arguments[self._index]
        self._index += 1
        return result

    def peek(self):
        return self._arguments[self._index]
