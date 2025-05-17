from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.offers_by_payment_method_view import Ui_OffersByPaymentMethodView


class OffersByPaymentMethodView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_OffersByPaymentMethodView()
        self.ui.setupUi(self)
