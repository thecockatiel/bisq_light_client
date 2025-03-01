#!/usr/bin/env python3
# -*- mode: python -*-
import sys
from utils.common_checks import do_common_checks

do_common_checks()


from utils.pb_helper import check_and_use_pure_python_pb_implementation

check_and_use_pure_python_pb_implementation()


from bisq.cli.cli_main import CliMain

if __name__ == "__main__":
    CliMain.main(sys.argv[1:])
