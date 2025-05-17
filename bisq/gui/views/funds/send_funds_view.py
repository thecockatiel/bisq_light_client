from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.send_funds_view import Ui_SendFundsView


class SendFundsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SendFundsView()
        self.ui.setupUi(self)
