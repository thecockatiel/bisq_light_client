from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.trade_process_normal_step import Ui_TradeProcessNormalStep

class TradeProcessNormalStep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TradeProcessNormalStep()
        self.ui.setupUi(self)
