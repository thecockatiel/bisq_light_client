import os
import subprocess
import sys


# used by is_python_pb_impl_required
def _is_python_pb_impl_required_check():
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
            return True
    return False


def is_python_pb_impl_required():
    if "PB_HELPER_PATH" in os.environ:
        raise RuntimeError("we are in a subprocess, this should not happen")
    # Use the file's absolute path dynamically.
    pb_helper_path = os.path.abspath(__file__)
    command = [
        sys.executable,
        "-c",
        (
            "import runpy, os; "
            "pb_file = os.environ['PB_HELPER_PATH']; "
            "ns = runpy.run_path(pb_file, run_name='__main__'); "
            "(ns['_is_python_pb_impl_required_check']() and os._exit(1)) or os._exit(0)"
        ),
    ]
    env = os.environ.copy()
    env["PB_HELPER_PATH"] = pb_helper_path
    result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL)
    # if process exits with 1, it means it is required
    return result.returncode == 1


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
        if _is_python_pb_impl_required_check():
            raise AssertionError(
                "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION change did not work. \n"
                "This is a fatal error. \n"
                "Exiting now..."
            )
