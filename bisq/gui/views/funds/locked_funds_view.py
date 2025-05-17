from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.locked_funds_view import Ui_LockedFundsView


class LockedFundsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_LockedFundsView()
        self.ui.setupUi(self)
