from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.my_open_offers_view import Ui_MyOpenOffersView


class MyOpenOffersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MyOpenOffersView()
        self.ui.setupUi(self)
