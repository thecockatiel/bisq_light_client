#!/usr/bin/env python3
# -*- mode: python -*-
import sys
from utils.common_checks import do_common_checks

do_common_checks()

from bisq.cli.cli_main import CliMain

if __name__ == "__main__":
    CliMain.main(sys.argv[1:])
