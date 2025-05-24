from datetime import datetime
from PyQt5.QtWidgets import QDialog, QListWidgetItem
from bisq.core.locale.res import Res
from bisq.gui.components.chat_bubble import ChatBubble, ChatSender
from bisq.gui.ui.out.trader_chat_dialog import Ui_TraderChatDialog

import pb_pb2 as protobuf
from utils.formatting import get_short_id


class TraderChatDialog(QDialog):
    def __init__(self, trade_id: str, parent=None):
        super().__init__(parent)
        self.ui = Ui_TraderChatDialog()
        self.ui.setupUi(self)
        self.trade_id = trade_id
        self.setWindowTitle(Res.get("tradeChat.chatWindowTitle", get_short_id(self.trade_id)))

    def add_chat_item(self, chat_message: protobuf.ChatMessage, chat_sender: ChatSender):
        item = QListWidgetItem()
        widget = ChatBubble(chat_message, chat_sender)
        sizehint = widget.sizeHint()
        sizehint.setWidth(0)
        item.setSizeHint(sizehint)
        self.ui.message_list_widget.addItem(item)
        self.ui.message_list_widget.setItemWidget(item, widget)
