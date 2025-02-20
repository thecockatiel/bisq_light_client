import os


def is_python_pb_impl_required():
    from pb_pb2 import GetInventoryResponse

    original = GetInventoryResponse(
        inventory={"1": "1", "2": "2", "3": "3"}
    ).SerializeToString()
    for i in range(10):
        # we need to test it 10 times quickly, because it is non deterministic
        inv = dict(GetInventoryResponse.FromString(original).inventory)
        test = GetInventoryResponse(inventory=inv).SerializeToString()
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

