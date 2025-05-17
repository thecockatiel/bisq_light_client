from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.start_view import Ui_StartView

class StartView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_StartView()
        self.ui.setupUi(self)
