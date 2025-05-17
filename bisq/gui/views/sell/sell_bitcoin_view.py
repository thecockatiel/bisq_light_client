from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.sell_bitcoin_view import Ui_SellBitcoinView


class SellBitcoinView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SellBitcoinView()
        self.ui.setupUi(self)
