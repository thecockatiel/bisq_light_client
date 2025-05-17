from typing import Optional
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPixmap, QColor, QPalette

from bisq.gui.dialogs.open_url_dialog import OpenUrlDialog
from bisq.gui.ui.out.trade_details import Ui_TradeDetails
from bisq.gui.utils.click_filter import ClickFilter


class TradeDetails(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TradeDetails()
        self.ui.setupUi(self)
        self.ui.remaining_time_edit.setCursorPosition(0)
        self.ui.open_explorer_btn.clicked.connect(
            self.open_deposit_tx_on_block_explorer
        )
        self._deposit_edit_click_filter = ClickFilter(self.ui.open_explorer_btn.click)
        self.ui.deposit_transaction_id_edit.installEventFilter(
            self._deposit_edit_click_filter
        )
        self.ui.copy_tx_id_btn.clicked.connect(self.copy_deposit_tx)
        self.set_progress_filled_red()

    def copy_deposit_tx(self):
        QApplication.clipboard().setText(self.ui.deposit_transaction_id_edit.text())

    def set_deposit_tx(self, value: str):
        self.ui.deposit_transaction_id_edit.setText(value)

    def set_progress_filled_red(self):
        self.ui.trade_period_progress_bar.setValue(
            self.ui.trade_period_progress_bar.maximum()
        )
        pallet = self.ui.trade_period_progress_bar.palette()
        pallet.setColor(QPalette.ColorRole.Highlight, QColor(150, 0, 0))
        self.ui.trade_period_progress_bar.setPalette(pallet)

    def open_deposit_tx_on_block_explorer(self):
        # TODO: show open in browser dialog and save user preference
        self.open_block_explorer(self.ui.deposit_transaction_id_edit.text())

    def open_block_explorer(self, tx_id: str):
        if tx_id:
            OpenUrlDialog.open_if_necessary(
                f"https://live.blockcypher.com/btc-testnet/tx/{tx_id}"
            )  # TODO: block explorer url must come from preferences

    def set_deposit_tx_id(self, tx_id: str):
        self.ui.deposit_transaction_id_edit.setText(tx_id)

    def set_confirmations(self, count: int):
        self.ui.confirmations_label.setToolTip(f"{count} confirmations")
        if count == 0:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/wait"))
        elif count == 1:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/clock1"))
        elif count == 2:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/clock2"))
        elif count == 3:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/clock3"))
        elif count == 4:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/clock4"))
        elif count == 5:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/clock5"))
        elif count > 5:
            self.ui.confirmations_label.setPixmap(QPixmap(":/icons/check-circle"))
