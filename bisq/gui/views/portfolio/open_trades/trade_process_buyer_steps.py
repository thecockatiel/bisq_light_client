from PyQt5.QtWidgets import (
    QWidget,
)
from PyQt5.QtCore import Qt

from bisq.gui.ui.out.trade_process_buyer_steps import Ui_TradeProcessBuyerSteps


class TradeProcessBuyerSteps(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TradeProcessBuyerSteps()
        self.ui.setupUi(self)
        self.ui.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
