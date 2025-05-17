from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.offers_by_currency_view import Ui_OffersByCurrencyView


class OffersByCurrencyView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_OffersByCurrencyView()
        self.ui.setupUi(self)
