from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.transactions_view import Ui_TransactionsView


class TransactionsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TransactionsView()
        self.ui.setupUi(self)
