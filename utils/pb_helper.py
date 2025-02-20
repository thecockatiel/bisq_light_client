import os
from importlib import reload
import pb_pb2 as protobuf


def is_python_pb_impl_required():
    original = protobuf.GetInventoryResponse(
        inventory={"1": "1", "2": "2", "3": "3"}
    ).SerializeToString()
    for i in range(10):
        # we need to test it 10 times quickly, because it is non deterministic
        inv = dict(protobuf.GetInventoryResponse.FromString(original).inventory)
        test = protobuf.GetInventoryResponse(inventory=inv).SerializeToString()
        if test != original:
            return True
    return False


def check_and_use_pure_python_pb_implementation(print_warning=True):
    if is_python_pb_impl_required():
        if print_warning:
            # fmt: off
            print("######################################################################")
            print("######################################################################")
            print("###   Setting PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION to 'python'   ###")
            print("###                    Expect Degraded Performance                 ###")
            print("######################################################################")
            print("######################################################################")
            # fmt: on
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = (
            "python"  # Prevents using cpp implementation of protobuf, and thus prevents the random dictionary order issue
        )
        reload(protobuf)

        if is_python_pb_impl_required():
            raise AssertionError(
                "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION change did not work. \n"
                "This is a fatal error. \n"
                "Exiting now..."
            )
