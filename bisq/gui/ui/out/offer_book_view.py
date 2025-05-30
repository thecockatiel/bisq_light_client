# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/mnt/projects/thecockatiel/bisq_lc/bisq/gui/ui/offer_book_view.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_OfferBookView(object):
    def setupUi(self, OfferBookView):
        OfferBookView.setObjectName("OfferBookView")
        OfferBookView.resize(864, 523)
        self.verticalLayout = QtWidgets.QVBoxLayout(OfferBookView)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_4 = QtWidgets.QLabel(OfferBookView)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.selected_currency_combobox = QtWidgets.QComboBox(OfferBookView)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selected_currency_combobox.sizePolicy().hasHeightForWidth())
        self.selected_currency_combobox.setSizePolicy(sizePolicy)
        self.selected_currency_combobox.setMinimumSize(QtCore.QSize(240, 0))
        self.selected_currency_combobox.setEditable(True)
        self.selected_currency_combobox.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.selected_currency_combobox.setFrame(True)
        self.selected_currency_combobox.setObjectName("selected_currency_combobox")
        self.horizontalLayout_3.addWidget(self.selected_currency_combobox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.chart_holder = QtWidgets.QWidget(OfferBookView)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.chart_holder.sizePolicy().hasHeightForWidth())
        self.chart_holder.setSizePolicy(sizePolicy)
        self.chart_holder.setMinimumSize(QtCore.QSize(0, 220))
        self.chart_holder.setMaximumSize(QtCore.QSize(16777215, 360))
        self.chart_holder.setObjectName("chart_holder")
        self.chart_holder_layout = QtWidgets.QVBoxLayout(self.chart_holder)
        self.chart_holder_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_holder_layout.setSpacing(0)
        self.chart_holder_layout.setObjectName("chart_holder_layout")
        self.verticalLayout.addWidget(self.chart_holder)
        self.lists_holder = QtWidgets.QWidget(OfferBookView)
        self.lists_holder.setObjectName("lists_holder")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.lists_holder)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.sell_block = QtWidgets.QWidget(self.lists_holder)
        self.sell_block.setObjectName("sell_block")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.sell_block)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.sell_block)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.sell_btc_button = QtWidgets.QPushButton(self.sell_block)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(98, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(98, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(98, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        self.sell_btc_button.setPalette(palette)
        self.sell_btc_button.setObjectName("sell_btc_button")
        self.horizontalLayout_2.addWidget(self.sell_btc_button)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.sell_btc_table = QtWidgets.QTableView(self.sell_block)
        self.sell_btc_table.setObjectName("sell_btc_table")
        self.verticalLayout_4.addWidget(self.sell_btc_table)
        self.horizontalLayout.addWidget(self.sell_block)
        self.buy_block = QtWidgets.QWidget(self.lists_holder)
        self.buy_block.setObjectName("buy_block")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.buy_block)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_3 = QtWidgets.QLabel(self.buy_block)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_4.addWidget(self.label_3)
        self.buy_btc_button = QtWidgets.QPushButton(self.buy_block)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 111, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 111, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 111, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        self.buy_btc_button.setPalette(palette)
        self.buy_btc_button.setObjectName("buy_btc_button")
        self.horizontalLayout_4.addWidget(self.buy_btc_button)
        self.verticalLayout_6.addLayout(self.horizontalLayout_4)
        self.buy_btc_table = QtWidgets.QTableView(self.buy_block)
        self.buy_btc_table.setObjectName("buy_btc_table")
        self.verticalLayout_6.addWidget(self.buy_btc_table)
        self.horizontalLayout.addWidget(self.buy_block)
        self.verticalLayout.addWidget(self.lists_holder)

        self.retranslateUi(OfferBookView)
        QtCore.QMetaObject.connectSlotsByName(OfferBookView)

    def retranslateUi(self, OfferBookView):
        _translate = QtCore.QCoreApplication.translate
        OfferBookView.setWindowTitle(_translate("OfferBookView", "Form"))
        self.label_4.setText(_translate("OfferBookView", "Currency"))
        self.label.setText(_translate("OfferBookView", "Sell BTC to"))
        self.sell_btc_button.setText(_translate("OfferBookView", "Sell BTC"))
        self.label_3.setText(_translate("OfferBookView", "Buy BTC from"))
        self.buy_btc_button.setText(_translate("OfferBookView", "Buy BTC"))
