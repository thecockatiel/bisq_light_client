from abc import ABC

class AddOncePayload(ABC):
    """Marker interface for messages which must not be added again after a remove message has been received (e.g. MailboxMessages)."""
    pass