# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/mnt/projects/thecockatiel/bisq_lc/bisq/gui/ui/chat_bubble.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ChatBubble(object):
    def setupUi(self, ChatBubble):
        ChatBubble.setObjectName("ChatBubble")
        ChatBubble.resize(609, 341)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ChatBubble.sizePolicy().hasHeightForWidth())
        ChatBubble.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(ChatBubble)
        self.verticalLayout.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.date_label = QtWidgets.QLabel(ChatBubble)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.date_label.setFont(font)
        self.date_label.setStyleSheet(".QLabel {\n"
"  color: #aaaaaa;\n"
"}")
        self.date_label.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.date_label.setObjectName("date_label")
        self.verticalLayout.addWidget(self.date_label)
        self.message_label = QtWidgets.QLabel(ChatBubble)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message_label.sizePolicy().hasHeightForWidth())
        self.message_label.setSizePolicy(sizePolicy)
        self.message_label.setStyleSheet(".QLabel {\n"
" background-color: palette(mid);\n"
" color: palette(base);\n"
" border: 1px solid transparent;\n"
" border-radius: 8px;\n"
" padding: 6px;\n"
"}")
        self.message_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.message_label.setObjectName("message_label")
        self.verticalLayout.addWidget(self.message_label)
        self.message_delivery_label = QtWidgets.QLabel(ChatBubble)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.message_delivery_label.setFont(font)
        self.message_delivery_label.setStyleSheet(".QLabel {\n"
" color: #aaaaaa;\n"
"}")
        self.message_delivery_label.setScaledContents(True)
        self.message_delivery_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.message_delivery_label.setObjectName("message_delivery_label")
        self.verticalLayout.addWidget(self.message_delivery_label)

        self.retranslateUi(ChatBubble)
        QtCore.QMetaObject.connectSlotsByName(ChatBubble)

    def retranslateUi(self, ChatBubble):
        _translate = QtCore.QCoreApplication.translate
        ChatBubble.setWindowTitle(_translate("ChatBubble", "Form"))
        self.date_label.setText(_translate("ChatBubble", "22 May 2025 16:00:00"))
        self.message_label.setText(_translate("ChatBubble", "You can communicate with your trade peer to resolve potential problems with this trade.\n"
"  It is not mandatory to reply in the chat.\n"
"  If a trader violates any of the rules below, open a dispute and report it to the mediator or arbitrator.\n"
"  Chat rules:\n"
"  ● Do not send any links (risk of malware). You can send the transaction ID and the name of a block explorer.\n"
"  ● Do not send your seed words, private keys, passwords or other sensitive information!\n"
"  ● Do not encourage trading outside of Bisq (no security).\n"
"  ● Do not engage in any form of social engineering scam attempts.\n"
"  ● If a peer is not responding and prefers to not communicate via chat, respect their decision.\n"
"  ● Keep conversation scope limited to the trade. This chat is not a messenger replacement or troll-box.\n"
"  ● Keep conversation friendly and respectful."))
        self.message_delivery_label.setText(_translate("ChatBubble", "Message saved in receiver\'s mailbox"))
