import os

def is_pb_map_order_preserved():
    """must not be run on current process, otherwise defeats the point of checking"""
    import pb_pb2 as protobuf

    original = protobuf.GetInventoryResponse(
        inventory={"1": "1", "2": "2", "3": "3"}
    ).SerializeToString()
    for i in range(20):
        # we need to test it 10 times quickly, because it is non deterministic
        inv = dict(protobuf.GetInventoryResponse.FromString(original).inventory)
        test = protobuf.GetInventoryResponse(inventory=inv).SerializeToString()
        if test != original:
            return False
    return True

def is_python_pb_impl_required():
    # grpc version < 1.49.0 has a bug that causes map order to be lost during serialization
    # after 1.49 it still happens, but it seems so rare that we can probaby tolerate it
    # TODO: we have to check if this is really rare or not later
    import grpc
    try:
        version = grpc.__version__
        version = version.split('.')
        major, minor = int(version[0]), int(version[1])
        if major > 1 or (major == 1 and minor > 48):
            return False
    except:
        pass
    return True

def use_pure_python_pb_implementation():
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

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

        use_pure_python_pb_implementation()

        # Now we can run the check again to make sure it worked
        if not is_pb_map_order_preserved():
            raise AssertionError(
                "Protobuf map order was not preserved after check. \n"
                "This is a fatal error. \n"
                "Exiting now..."
            )
