from typing import Optional
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
import grpc_pb2
from utils.argparse_ext import parse_bool


class EditOfferOptionParser(SimpleMethodOptionParser):
    OPT_ENABLE_ON = 1
    OPT_ENABLE_OFF = 0
    OPT_ENABLE_IGNORED = -1

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.edit_offer_type: Optional[grpc_pb2.EditOfferRequest.EditType] = None
        self.parser.add_argument(
            f"--{OptLabel.OPT_FIXED_PRICE}",
            help="fixed btc price",
            dest=OptLabel.OPT_FIXED_PRICE,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_MKT_PRICE_MARGIN}",
            help="market btc price margin (%)",
            dest=OptLabel.OPT_MKT_PRICE_MARGIN,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_TRIGGER_PRICE}",
            help="trigger price (applies to mkt price margin based offers)",
            dest=OptLabel.OPT_TRIGGER_PRICE,
            type=str,
        )
        # The 'enable' string opt is optional, and can be empty (meaning do not change
        # activation state).  For this reason, a boolean type is not used (can only be
        # true or false).
        self.parser.add_argument(
            f"--{OptLabel.OPT_ENABLE}",
            help="enable or disable offer",
            dest=OptLabel.OPT_ENABLE,
            type=str,
            const="",
            nargs="?",
        )

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        has_no_edit_details = (
            OptLabel.OPT_FIXED_PRICE not in self.options
            and OptLabel.OPT_MKT_PRICE_MARGIN not in self.options
            and OptLabel.OPT_TRIGGER_PRICE not in self.options
            and OptLabel.OPT_ENABLE not in self.options
        )

        if has_no_edit_details:
            raise IllegalArgumentException("no edit details specified")

        if OptLabel.OPT_ENABLE in self.options:
            if self.value_not_specified(OptLabel.OPT_ENABLE):
                raise IllegalArgumentException(
                    "invalid enable value specified, must be true|false"
                )

            try:
                enable_opt_value = parse_bool(self.options.get(OptLabel.OPT_ENABLE))
            except:
                raise IllegalArgumentException(
                    "invalid enable value specified, must be true|false"
                )

            # A single enable opt is a valid opt combo.

            enable_opt_is_only_opt = (
                OptLabel.OPT_FIXED_PRICE not in self.options
                and OptLabel.OPT_MKT_PRICE_MARGIN not in self.options
                and OptLabel.OPT_TRIGGER_PRICE not in self.options
            )
            if enable_opt_is_only_opt:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.ACTIVATION_STATE_ONLY
                )
                return self

        if OptLabel.OPT_FIXED_PRICE in self.options:
            if self.value_not_specified(OptLabel.OPT_FIXED_PRICE):
                raise IllegalArgumentException("no fixed price specified")

            fixed_price = self.options.get(OptLabel.OPT_FIXED_PRICE, "0")
            self.verify_string_is_valid_float(fixed_price)

            fixed_price_opt_is_only_opt = (
                OptLabel.OPT_MKT_PRICE_MARGIN not in self.options
                and OptLabel.OPT_TRIGGER_PRICE not in self.options
                and OptLabel.OPT_ENABLE not in self.options
            )
            if fixed_price_opt_is_only_opt:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_ONLY
                )
                return self

            fixed_price_and_enable_opt_are_only_opts = (
                OptLabel.OPT_ENABLE in self.options
                and OptLabel.OPT_MKT_PRICE_MARGIN not in self.options
                and OptLabel.OPT_TRIGGER_PRICE not in self.options
            )
            if fixed_price_and_enable_opt_are_only_opts:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_AND_ACTIVATION_STATE
                )
                return self

        if OptLabel.OPT_MKT_PRICE_MARGIN in self.options:
            if self.value_not_specified(OptLabel.OPT_MKT_PRICE_MARGIN):
                raise IllegalArgumentException("no market price margin specified")

            price_margin_pct_as_string = self.options.get(
                OptLabel.OPT_MKT_PRICE_MARGIN, "0.00"
            )

            self.verify_string_is_valid_float(price_margin_pct_as_string)

            mkt_price_margin_opt_is_only_opt = (
                OptLabel.OPT_TRIGGER_PRICE not in self.options
                and OptLabel.OPT_FIXED_PRICE not in self.options
                and OptLabel.OPT_ENABLE not in self.options
            )
            if mkt_price_margin_opt_is_only_opt:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_ONLY
                )
                return self

            mkt_price_margin_opt_and_enable_opt_are_only_opts = (
                OptLabel.OPT_ENABLE in self.options
                and OptLabel.OPT_FIXED_PRICE not in self.options
                and OptLabel.OPT_TRIGGER_PRICE not in self.options
            )
            if mkt_price_margin_opt_and_enable_opt_are_only_opts:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_ACTIVATION_STATE
                )
                return self

        if OptLabel.OPT_TRIGGER_PRICE in self.options:
            if self.value_not_specified(OptLabel.OPT_TRIGGER_PRICE):
                raise IllegalArgumentException("no trigger price specified")

            trigger_price = self.options.get(OptLabel.OPT_TRIGGER_PRICE, "0")

            self.verify_string_is_valid_float(trigger_price)

            trigger_price_opt_is_only_opt = (
                OptLabel.OPT_MKT_PRICE_MARGIN not in self.options
                and OptLabel.OPT_FIXED_PRICE not in self.options
                and OptLabel.OPT_ENABLE not in self.options
            )
            if trigger_price_opt_is_only_opt:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_ONLY
                )
                return self

            trigger_price_opt_and_enable_opt_are_only_opts = (
                OptLabel.OPT_ENABLE in self.options
                and OptLabel.OPT_MKT_PRICE_MARGIN not in self.options
                and OptLabel.OPT_FIXED_PRICE not in self.options
            )
            if trigger_price_opt_and_enable_opt_are_only_opts:
                self.edit_offer_type = (
                    grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_AND_ACTIVATION_STATE
                )
                return self

        if (
            OptLabel.OPT_MKT_PRICE_MARGIN in self.options
            and OptLabel.OPT_FIXED_PRICE in self.options
        ):
            raise IllegalArgumentException(
                "cannot specify market price margin and fixed price"
            )

        if (
            OptLabel.OPT_FIXED_PRICE in self.options
            and OptLabel.OPT_TRIGGER_PRICE in self.options
        ):
            raise IllegalArgumentException(
                "trigger price cannot be set on fixed price offers"
            )

        if (
            OptLabel.OPT_MKT_PRICE_MARGIN in self.options
            and OptLabel.OPT_TRIGGER_PRICE in self.options
            and OptLabel.OPT_ENABLE not in self.options
        ):
            self.edit_offer_type = (
                grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE
            )
            return self

        if (
            OptLabel.OPT_MKT_PRICE_MARGIN in self.options
            and OptLabel.OPT_TRIGGER_PRICE in self.options
            and OptLabel.OPT_ENABLE in self.options
        ):
            self.edit_offer_type = (
                grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE_AND_ACTIVATION_STATE
            )
            return self

        return self

    def get_fixed_price(self) -> str:
        if self.edit_offer_type in [
            grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_ONLY,
            grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_AND_ACTIVATION_STATE,
        ]:
            return self.options.get(OptLabel.OPT_FIXED_PRICE, "0") or "0"
        else:
            return "0"

    def get_trigger_price(self) -> str:
        if self.edit_offer_type in [
            grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_ONLY,
            grpc_pb2.EditOfferRequest.EditType.TRIGGER_PRICE_AND_ACTIVATION_STATE,
            grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE,
            grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE_AND_ACTIVATION_STATE,
        ]:
            return self.options.get(OptLabel.OPT_TRIGGER_PRICE, "0") or "0"
        else:
            return "0"

    def get_mkt_price_margin(self) -> str:
        if self.edit_offer_type in [
            grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_ONLY,
            grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_ACTIVATION_STATE,
            grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE,
            grpc_pb2.EditOfferRequest.EditType.MKT_PRICE_MARGIN_AND_TRIGGER_PRICE_AND_ACTIVATION_STATE,
        ]:
            return self.options.get(OptLabel.OPT_MKT_PRICE_MARGIN, "0.00") or "0.00"
        else:
            return "0.00"

    def get_mkt_price_margin_pct(self) -> float:
        return float(self.options.get(OptLabel.OPT_MKT_PRICE_MARGIN, "0.00") or "0.00")

    def is_using_mkt_price_margin(self) -> bool:
        # We do not have the offer, so we do not really know if is_using_mkt_price_margin
        # should be true or false if editType = ACTIVATION_STATE_ONLY. Take care to
        # override this value in the daemon in the ACTIVATION_STATE_ONLY case.
        return self.edit_offer_type not in [
            grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_ONLY,
            grpc_pb2.EditOfferRequest.EditType.FIXED_PRICE_AND_ACTIVATION_STATE,
        ]

    def get_enable_as_signed_int(self) -> int:
        # Client sends sint32 in grpc request, not a bool that can only be true or false.
        # If enable = -1, do not change activation state
        # If enable =  0, set state = AVAILABLE
        # If enable =  1, set state = DEACTIVATED
        input = self.is_enable()
        return (
            EditOfferOptionParser.OPT_ENABLE_IGNORED
            if input is None
            else (
                EditOfferOptionParser.OPT_ENABLE_ON
                if input
                else EditOfferOptionParser.OPT_ENABLE_OFF
            )
        )

    def is_enable(self) -> Optional[bool]:
        return (
            parse_bool(self.options.get(OptLabel.OPT_ENABLE))
            if self.options.get(OptLabel.OPT_ENABLE, None)
            else None
        )

    def get_offer_edit_type(self) -> grpc_pb2.EditOfferRequest.EditType:
        return self.edit_offer_type
