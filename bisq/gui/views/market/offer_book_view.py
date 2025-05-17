from PyQt5.QtWidgets import (
    QWidget,
)
import numpy as np
from bisq.gui.components.charts.offer_book_chart import OfferBookChart
from bisq.gui.ui.out.offer_book_view import Ui_OfferBookView


class OfferBookView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_OfferBookView()
        self.ui.setupUi(self)
        self.offer_book_chart = OfferBookChart()
        self.ui.chart_holder_layout.addWidget(self.offer_book_chart)
        sell_prices = np.array([53000, 53500, 55400, 55600, 55600, 60000, 63400])
        sell_volumes = np.array([0.51, 0.42, 0.39, 0.37, 0.36, 0.36, 0.25])

        buy_prices = np.array(
            [65500, 65700, 66700, 68000, 69000, 70000, 70100, 70200, 71200]
        )
        buy_volumes = np.array([0.08, 0.12, 0.25, 0.27, 0.35, 0.75, 0.75, 0.75, 1.00])

        self.offer_book_chart.updatePlot(
            sell_prices, sell_volumes, buy_prices, buy_volumes
        )
