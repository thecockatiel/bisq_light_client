from bisq.core.notifications.mobile_message_type import MobileMessageType
from utils.time import get_time_ms


class MobileMessage:

    def __init__(
        self,
        title: str,
        message: str,
        mobile_message_type: MobileMessageType,
        tx_id: str = "",
    ):
        assert mobile_message_type is not None
        assert tx_id is not None

        self.title = title
        self.message = message
        self.tx_id = tx_id
        self.mobile_message_type = mobile_message_type  # transient

        self.type = mobile_message_type.name
        self.action_required = ""
        self.sent_date = get_time_ms()
        self.version = 1

    def get_json_dict(self):
        return {
            "sentDate": self.sent_date,
            "txId": self.tx_id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "actionRequired": self.action_required,
            "version": self.version,
        }
