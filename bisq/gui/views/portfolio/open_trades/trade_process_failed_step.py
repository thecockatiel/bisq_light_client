from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.trade_process_failed_step import Ui_TradeProcessFailedStep

class TradeProcessFailedStep(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TradeProcessFailedStep()
        self.ui.setupUi(self)
