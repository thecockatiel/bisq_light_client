from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.components.qr_code_widget import QRCodeWidget
from bisq.gui.ui.out.receive_funds_view import Ui_ReceiveFundsView


class ReceiveFundsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ReceiveFundsView()
        self.ui.setupUi(self)
        self.ui.receive_qr_layout.addWidget(
            QRCodeWidget(
                "bitcoin:placeholder_address?label=Fund Bisq wallet"
            )
        )
