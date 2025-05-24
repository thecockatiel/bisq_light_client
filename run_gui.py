import os

os.environ["QT_API"] = "pyqt5"  # import early to avoid problems

import sys
import asyncio
from bisq.core.locale.res import Res
from bisq.common.config.config import Config
from utils.dir import user_data_dir
from PyQt5.QtWidgets import QApplication
from bisq.gui.main_window import MainWindow
from qasync import QEventLoop, QApplication

if __name__ == "__main__":
    config = Config("bisq_light", user_data_dir())
    Res.setup(config) # TODO: move Res and dep tree into common ?

    app = QApplication(sys.argv)
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)


    # with GrpcClient(host, port, password) as grpc_client:

    widget = MainWindow()
    widget.show()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())
