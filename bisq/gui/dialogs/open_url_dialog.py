from PyQt5.QtWidgets import QDialog, QPushButton, QDialogButtonBox, QApplication
from bisq.gui.ui.out.open_url_dialog import Ui_OpenUrlDialog
import webbrowser

from qasync import asyncSlot

_settings_key = "open_url_without_asking"


class OpenUrlDialog(QDialog):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.ui = Ui_OpenUrlDialog()
        self.ui.setupUi(self)
        self.ui.url_label.setText(url)
        ok_button = QPushButton("Open the web page and don't ask again")
        cancel_button = QPushButton("Copy url and cancel")
        self.ui.button_box.addButton(ok_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self.ui.button_box.addButton(
            cancel_button, QDialogButtonBox.ButtonRole.RejectRole
        )

        self.ui.button_box.accepted.connect(self.open_and_remember)
        self.ui.button_box.rejected.connect(self.cancel_and_copy)

    def open_and_remember(self):
        # set_cookie(_settings_key, True)
        webbrowser.open(self.ui.url_label.text())
        self.accept()

    def cancel_and_copy(self):
        QApplication.clipboard().setText(self.ui.url_label.text())
        self.reject()

    @staticmethod
    def open_if_necessary(url: str):
        if not url:
            raise ValueError("url was not set at OpenUrlDialog")
        # if get_cookie(_settings_key, False):
        #     webbrowser.open(url)
        #     return

        OpenUrlDialog(url).exec()
    
