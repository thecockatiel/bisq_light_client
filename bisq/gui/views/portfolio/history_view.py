from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.history_view import Ui_HistoryView


class HistoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_HistoryView()
        self.ui.setupUi(self)
