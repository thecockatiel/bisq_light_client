
import argparse


class ConditionalArgumentAction(argparse.Action):
    def __init__(
        self,
        unavailable_if: list[str] = None,
        available_if: list[str] = None,
        needs: list[str] = None,
        *args,
        **kwargs,
    ):
        # checks are run later after parse
        self.unavailable_if = unavailable_if
        self.available_if = available_if
        self.needs = needs
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class DisabledArgumentAction(argparse.Action):
    def __init__(self, disable_message: str = None, *args, **kwargs):
        self.disable_message = disable_message
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        msg = self.disable_message or f"Option '{option_string}' is currently disabled"
        parser.error(msg)


class CustomArgumentParser(argparse.ArgumentParser):
    def add_disabled_argument(self, *args, disable_message: str = None, **kwargs):
        kwargs["action"] = DisabledArgumentAction
        kwargs["disable_message"] = disable_message
        return self.add_argument(*args, **kwargs)

    def add_conditional_argument(
        self,
        *args,
        unavailable_if: list[str] = None,
        available_if: list[str] = None,
        needs: list[str] = None,
        **kwargs,
    ):
        kwargs["action"] = ConditionalArgumentAction
        kwargs["unavailable_if"] = unavailable_if
        kwargs["available_if"] = available_if
        kwargs["needs"] = needs
        return self.add_argument(*args, **kwargs)

    def parse_known_args(self, *args, **kw_args):
        namespace, args = super().parse_known_args(*args, **kw_args)
        for action in self._actions:
            if isinstance(action, ConditionalArgumentAction):
                if (
                    action.unavailable_if
                    and getattr(namespace, action.dest) is not None
                ):
                    for arg in action.unavailable_if:
                        if getattr(namespace, arg):
                            self.error(
                                f"Option '{action.dest}' is not allowed when '{arg}' is present."
                            )
                if action.available_if and getattr(namespace, action.dest) is not None:
                    for arg in action.available_if:
                        if not getattr(namespace, arg):
                            self.error(
                                f"Option '{action.dest}' is not allowed when '{arg}' is not present."
                            )
                if action.needs and getattr(namespace, action.dest) is not None:
                    for arg in action.needs:
                        if not getattr(namespace, arg):
                            self.error(
                                f"Option '{action.dest}' requires '{arg}' to be present."
                                + (
                                    f" all needed options: {action.needs}"
                                    if len(action.needs) > 1
                                    else ""
                                )
                            )
        return namespace, args

    def parse_known_intermixed_args(self, *args, **kw_args):
        namespace, extras = super().parse_known_intermixed_args(*args, **kw_args)
        for action in self._actions:
            if isinstance(action, ConditionalArgumentAction):
                if (
                    action.unavailable_if
                    and getattr(namespace, action.dest) is not None
                ):
                    for arg in action.unavailable_if:
                        if getattr(namespace, arg):
                            self.error(
                                f"Option '{action.dest}' is not allowed when '{arg}' is present."
                            )
                if action.available_if and getattr(namespace, action.dest) is not None:
                    for arg in action.available_if:
                        if not getattr(namespace, arg):
                            self.error(
                                f"Option '{action.dest}' is not allowed when '{arg}' is not present."
                            )
                if action.needs and getattr(namespace, action.dest) is not None:
                    for arg in action.needs:
                        if not getattr(namespace, arg):
                            self.error(
                                f"Option '{action.dest}' requires '{arg}' to be present."
                                + (
                                    f" all needed options: {action.needs}"
                                    if len(action.needs) > 1
                                    else ""
                                )
                            )
        return namespace, extras