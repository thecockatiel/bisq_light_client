import inspect
import json
from typing import Any, Optional, Type
from bisq.cli.opts.opt_label import OptLabel
from bisq.cli.opts.simple_method_option_parser import SimpleMethodOptionParser
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from utils.custom_iterators import is_iterable
from utils.preconditions import check_argument
from pb_pb2 import NodeAddress, NetworkEnvelope


class SendProtoOptionParser(SimpleMethodOptionParser):

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.parser.add_argument(
            f"--{OptLabel.OPT_NODE_ADDRESS}",
            help="Full node address in format of host:port",
            dest=OptLabel.OPT_NODE_ADDRESS,
            type=str,
        )
        self.parser.add_argument(
            f"--{OptLabel.OPT_PROTO}",
            help="path to json file that contains proto definition",
            dest=OptLabel.OPT_PROTO,
            type=str,
        )
        self.node_address: Optional[NodeAddress] = None
        self.proto: Optional[NetworkEnvelope] = None

    def parse(self):
        super().parse()

        # Short circuit opt validation if user just wants help.
        if self.options.get(OptLabel.OPT_HELP, False):
            return self

        if not self.options.get(OptLabel.OPT_NODE_ADDRESS, None):
            raise IllegalArgumentException("no node-address specified")

        self.node_address = SendProtoOptionParser._from_full_address(
            self.options[OptLabel.OPT_NODE_ADDRESS]
        )

        if not self.options.get(OptLabel.OPT_PROTO, None):
            raise IllegalArgumentException("no proto file path specified")

        with open(self.options[OptLabel.OPT_PROTO], "r") as proto_file:
            data = json.load(proto_file)
            if not isinstance(data, dict):
                raise IllegalArgumentException(
                    "proto file must contain a single json object at root"
                )

            if data.get("message_version", None) is None:
                raise IllegalArgumentException(
                    "proto file must contain 'message_version' field at root of the object"
                )

            if len(data.keys()) != 2:
                raise IllegalArgumentException(
                    "proto file must contain only 'message_version' and a one of NetworkEnvelope field names"
                )

        # get other key than message_version
        envelope_field = next(iter(data.keys() - {"message_version"}))
        envelope_value = data[envelope_field]

        try:
            # get the class of the NetworkEnvelope field
            concrete_class = NetworkEnvelope.DESCRIPTOR.fields_by_name[
                envelope_field
            ].message_type._concrete_class
        except:
            raise IllegalStateException(
                "proto file must contain a valid NetworkEnvelope field name. given: "
                + envelope_field
            )

        try:
            envelope_proto = SendProtoOptionParser.recursively_make_proto_class(
                envelope_value, concrete_class
            )
        except Exception as e:
            raise IllegalStateException(
                "Failed to create proto class from given json: " + str(e)
            ) from e

        kw_args = {
            "message_version": data["message_version"],
            envelope_field: envelope_proto,
        }

        self.proto = NetworkEnvelope(**kw_args)

        return self

    @staticmethod
    def _from_full_address(full_address: str) -> "NodeAddress":
        # Handle IPv6 addresses
        if full_address.startswith("["):
            split = full_address.split("]")
            check_argument(len(split) == 2, "Invalid IPv6 address format")
            host_name = split[0][1:]  # Remove the leading '['
            port = int(split[1].replace(":", ""))
        else:
            # Handle IPv4 addresses and hostnames
            split = full_address.split(":")
            check_argument(len(split) == 2, "fullAddress must contain ':'")
            host_name = split[0]
            port = int(split[1])

        return NodeAddress(host_name=host_name, port=port)

    @staticmethod
    def recursively_make_proto_class(proto_dict: dict, concrete_class: Type):
        kw_args = {}
        for key, value in proto_dict.items():
            if isinstance(value, dict):
                try:
                    clazz = concrete_class.DESCRIPTOR.fields_by_name[
                        key
                    ].message_type._concrete_class
                except:
                    raise IllegalStateException(
                        f"Expected to find a concrete class on field '{key}' of {concrete_class.__class__.__name__}, but could not find one."
                    )
                kw_args[key] = SendProtoOptionParser.recursively_make_proto_class(
                    value, clazz
                )
            else:
                if is_iterable(value):
                    arr = []
                    for v in value:
                        if isinstance(v, dict):
                            try:
                                clazz = concrete_class.DESCRIPTOR.fields_by_name[
                                    key
                                ].message_type._concrete_class
                            except:
                                raise IllegalStateException(
                                    f"Expected to find a concrete class on field '{key}' of {concrete_class.__class__.__name__}, but could not find one."
                                )
                            arr.append(
                                SendProtoOptionParser.recursively_make_proto_class(
                                    v, clazz
                                )
                            )
                    kw_args[key] = arr
                else:
                    kw_args[key] = SendProtoOptionParser._to_binary_or_passthrough(
                        value
                    )

        return concrete_class(**kw_args)

    @staticmethod
    def _to_binary_or_passthrough(value: Any):
        if isinstance(value, str):
            if value.startswith("b'") and value.endswith("'"):
                return value[2:-1].encode("utf-8")
            if value.startswith("bh'") and value.endswith("'"):
                return bytes.fromhex(value[3:-1])
        return value
