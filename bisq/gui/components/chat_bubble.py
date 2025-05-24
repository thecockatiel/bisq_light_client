from datetime import datetime
from enum import IntEnum, auto
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QColor
from bisq.core.locale.res import Res
from bisq.gui.ui.out.chat_bubble import Ui_ChatBubble

import pb_pb2 as protobuf


class ChatSender(IntEnum):
    SYSTEM = auto()
    ME = auto()
    THEM = auto()


BASE_STYLESHEET = """
.QLabel {
 background-color: <bg>;
 color: <fg>;
 border: 1px solid transparent;
 border-radius: 8px;
 padding: 6px;
}
"""


class ChatBubble(QWidget):
    def __init__(
        self,
        chat_message: protobuf.ChatMessage,
        sender: ChatSender,
        parent=None,
    ):
        super().__init__(parent)
        self.ui = Ui_ChatBubble()
        self.ui.setupUi(self)
        self._set_chat_message(chat_message)
        self._set_chat_sender(sender)

    def _set_chat_message(self, chat_message: protobuf.ChatMessage):
        dt = datetime.fromtimestamp(chat_message.date / 1000)
        self.ui.date_label.setText(dt.strftime("%d %b %Y %H:%M:%S"))
        self.ui.message_label.setText(chat_message.message.replace("\t", "    "))
        if chat_message.acknowledged:
            self.ui.message_delivery_label.setText(Res.get("support.acknowledged"))
        elif chat_message.stored_in_mailbox:
            self.ui.message_delivery_label.setText(Res.get("support.savedInMailbox"))
        elif chat_message.ack_error:
            self.ui.message_delivery_label.setText(
                Res.get("support.error", chat_message.ack_error)
            )
            self.ui.message_delivery_label.setStyleSheet("color: red;")
        elif chat_message.arrived:
            self.ui.message_delivery_label.setText(Res.get("support.transient"))
        else:
            self.ui.message_delivery_label.setVisible(False)

    def _set_chat_sender(self, chat_sender: ChatSender):
        stylesheet = BASE_STYLESHEET.replace("<fg>", "#dde6ee")
        if chat_sender == ChatSender.SYSTEM:
            stylesheet = stylesheet.replace("<bg>", "#1a6e1e")
        elif chat_sender == ChatSender.ME:
            stylesheet = stylesheet.replace("<bg>", "#2b5278")
        else:
            stylesheet = stylesheet.replace("<bg>", "#1d2c3d")
        self.ui.message_label.setStyleSheet(stylesheet)
