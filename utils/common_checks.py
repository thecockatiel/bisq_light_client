import sys


MIN_PYTHON_VERSION = "3.9.0"


def do_common_checks():
    # Ensure that asserts are enabled. For sanity and paranoia, we require this.
    # Code *should not rely* on asserts being enabled. In particular, safety and security checks should
    # always explicitly raise exceptions. However, this rule is mistakenly broken occasionally...
    try:
        assert False  # noqa: B011
    except AssertionError:
        pass
    else:
        raise ImportError(
            "Running with asserts disabled. Refusing to continue. Exiting..."
        )

    _min_python_version_tuple = tuple(map(int, (MIN_PYTHON_VERSION.split("."))))

    if sys.version_info[:3] < _min_python_version_tuple:
        sys.exit(
            f"Error: Bisq light client requires Python version >= {MIN_PYTHON_VERSION}..."
        )
