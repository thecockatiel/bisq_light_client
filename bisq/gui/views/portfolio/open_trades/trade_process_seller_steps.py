from PyQt5.QtWidgets import (
    QWidget,
)
from PyQt5.QtCore import Qt

from bisq.gui.ui.out.trade_process_seller_steps import Ui_TradeProcessSellerSteps


class TradeProcessSellerSteps(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TradeProcessSellerSteps()
        self.ui.setupUi(self)
        self.ui.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
