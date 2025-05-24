from PyQt5.QtWidgets import (
    QMainWindow,
)
from bisq.common.version import Version
from bisq.gui.views.main_view import MainView
from bisq.gui.ui.out.main_window import Ui_MainWindow 
from qasync import asyncClose 


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.main_view = MainView()
        self.main_view.ui.version_label.setText(f"v{Version.VERSION}")
        self.ui.main_layout.addWidget(self.main_view)
        self.set_status("Ready")

    def set_status(self, text: str):
        self.main_view.ui.status_label.setText(text)

    @asyncClose
    async def closeEvent(self, event):
        pass
