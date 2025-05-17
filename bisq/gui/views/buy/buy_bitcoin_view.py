from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.buy_bitcoin_view import Ui_BuyBitcoinView


class BuyBitcoinView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_BuyBitcoinView()
        self.ui.setupUi(self)
