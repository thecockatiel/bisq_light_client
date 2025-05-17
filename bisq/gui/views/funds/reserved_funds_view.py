from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.reserved_funds_view import Ui_ReservedFundsView


class ReservedFundsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ReservedFundsView()
        self.ui.setupUi(self)
