#!/usr/bin/env python3
# -*- mode: python -*-
import sys

from utils.pb_helper import check_and_use_pure_python_pb_implementation

check_and_use_pure_python_pb_implementation(False)

MIN_PYTHON_VERSION = "3.9.0"
_min_python_version_tuple = tuple(map(int, (MIN_PYTHON_VERSION.split("."))))


if sys.version_info[:3] < _min_python_version_tuple:
    sys.exit(
        f"Error: Bisq light client requires Python version >= {MIN_PYTHON_VERSION}..."
    )

from bisq.cli.cli_main import CliMain

if __name__ == "__main__":
    CliMain.main(sys.argv[1:])
