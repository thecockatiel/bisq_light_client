# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/mnt/projects/thecockatiel/bisq_lc/bisq/gui/ui/history_view.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_HistoryView(object):
    def setupUi(self, HistoryView):
        HistoryView.setObjectName("HistoryView")
        HistoryView.resize(782, 558)
        self.verticalLayout = QtWidgets.QVBoxLayout(HistoryView)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_2 = QtWidgets.QLabel(HistoryView)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.history_filter_edit = QtWidgets.QLineEdit(HistoryView)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.history_filter_edit.sizePolicy().hasHeightForWidth())
        self.history_filter_edit.setSizePolicy(sizePolicy)
        self.history_filter_edit.setMinimumSize(QtCore.QSize(0, 0))
        self.history_filter_edit.setMaximumSize(QtCore.QSize(500, 16777215))
        self.history_filter_edit.setObjectName("history_filter_edit")
        self.horizontalLayout_3.addWidget(self.history_filter_edit)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.history_table_view = QtWidgets.QTableView(HistoryView)
        self.history_table_view.setObjectName("history_table_view")
        self.verticalLayout.addWidget(self.history_table_view)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_5 = QtWidgets.QLabel(HistoryView)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_6.addWidget(self.label_5)
        self.history_entries_count_label = QtWidgets.QLabel(HistoryView)
        self.history_entries_count_label.setObjectName("history_entries_count_label")
        self.horizontalLayout_6.addWidget(self.history_entries_count_label)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.retranslateUi(HistoryView)
        QtCore.QMetaObject.connectSlotsByName(HistoryView)

    def retranslateUi(self, HistoryView):
        _translate = QtCore.QCoreApplication.translate
        HistoryView.setWindowTitle(_translate("HistoryView", "Form"))
        self.label_2.setText(_translate("HistoryView", "Filter"))
        self.label_5.setText(_translate("HistoryView", "Number of entries:"))
        self.history_entries_count_label.setText(_translate("HistoryView", "0"))
