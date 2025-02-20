import os


def is_python_pb_impl_required():
    from pb_pb2 import GetInventoryResponse

    original = GetInventoryResponse(inventory={"1": "1", "2": "2"}).SerializeToString()
    inv = dict(GetInventoryResponse.FromString(original).inventory)
    test = GetInventoryResponse(inventory=inv).SerializeToString()
    if test != original:
        return True
    return False


def check_and_use_pure_python_pb_implementation():
    if is_python_pb_impl_required():
        print("######################################################################")
        print("######################################################################")
        print("###   Setting PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION to 'python'   ###")
        print("###                    Expect Degraded Performance                 ###")
        print("######################################################################")
        print("######################################################################")
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = (
            "python"  # Prevents using cpp implementation of protobuf, and thus prevents the random dictionary order issue
        )
