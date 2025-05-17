from PyQt5.QtWidgets import (
    QWidget,
)

from bisq.gui.ui.out.main_view import Ui_MainView
from bisq.gui.views.buy.buy_bitcoin_view import BuyBitcoinView
from bisq.gui.views.funds.locked_funds_view import LockedFundsView
from bisq.gui.views.funds.receive_funds_view import ReceiveFundsView
from bisq.gui.views.funds.reserved_funds_view import ReservedFundsView
from bisq.gui.views.funds.send_funds_view import SendFundsView
from bisq.gui.views.funds.transactions_view import TransactionsView
from bisq.gui.views.market.offer_book_view import OfferBookView
from bisq.gui.views.market.offers_by_currency_view import OffersByCurrencyView
from bisq.gui.views.market.offers_by_payment_method_view import (
    OffersByPaymentMethodView,
)
from bisq.gui.views.portfolio.history_view import HistoryView
from bisq.gui.views.portfolio.my_open_offers_view import MyOpenOffersView
from bisq.gui.views.portfolio.open_trades.open_trades_view import OpenTradesView
from bisq.gui.views.sell.sell_bitcoin_view import SellBitcoinView


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainView()
        self.ui.setupUi(self)

        # market tabs
        self.offer_book_view = OfferBookView()
        self.ui.offer_book_layout.addWidget(self.offer_book_view)
        self.offers_by_currency = OffersByCurrencyView()
        self.ui.offers_by_currency_layout.addWidget(self.offers_by_currency)
        self.offers_by_payment_method = OffersByPaymentMethodView()
        self.ui.offers_by_payment_layout.addWidget(self.offers_by_payment_method)

        # buy tabs
        self.buy_bitcoin_view = BuyBitcoinView()
        self.ui.buy_bitcoin_layout.addWidget(self.buy_bitcoin_view)

        # sell tabs
        self.sell_bitcoin_view = SellBitcoinView()
        self.ui.sell_bitcoin_layout.addWidget(self.sell_bitcoin_view)

        # portfolio tabs
        self.my_open_offers_view = MyOpenOffersView()
        self.ui.portfolio_my_offers_tab.layout().addWidget(self.my_open_offers_view)
        self.open_trades_view = OpenTradesView()
        self.ui.portfolio_open_trades_tab.layout().addWidget(self.open_trades_view)
        self.history_view = HistoryView()
        self.ui.portfolio_history_tab.layout().addWidget(self.history_view)

        # funds tabs
        self.receive_funds_view = ReceiveFundsView()
        self.ui.receive_funds_layout.addWidget(self.receive_funds_view)
        self.send_funds_view = SendFundsView()
        self.ui.send_funds_layout.addWidget(self.send_funds_view)
        self.reserved_funds_view = ReservedFundsView()
        self.ui.reserved_funds_layout.addWidget(self.reserved_funds_view)
        self.locked_funds_view = LockedFundsView()
        self.ui.locked_funds_layout.addWidget(self.locked_funds_view)
        self.transactions_view = TransactionsView()
        self.ui.transactions_layout.addWidget(self.transactions_view)
