from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.open_trades_view import Ui_OpenTradesView
from bisq.gui.views.portfolio.open_trades.trade_details import TradeDetails
from bisq.gui.views.portfolio.open_trades.trade_process_buyer_steps import (
    TradeProcessBuyerSteps,
)
from bisq.gui.views.portfolio.open_trades.trade_process_normal_step import (
    TradeProcessNormalStep,
)


class OpenTradesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_OpenTradesView()
        self.ui.setupUi(self)

        self.buyer_steps = TradeProcessBuyerSteps()
        self.ui.trade_step_and_details_layout.addWidget(self.buyer_steps)
        self.buyer_steps.ui.trade_process_step_layout.addWidget(
            TradeProcessNormalStep(), 1
        )

        self.trade_details = TradeDetails()
        self.ui.trade_step_and_details_layout.addWidget(self.trade_details, 2)
