from abc import ABC, abstractmethod


class SendMailboxMessageListener(ABC):

    @abstractmethod
    def on_arrived(self):
        pass

    @abstractmethod
    def on_stored_in_mailbox(self):
        pass

    @abstractmethod
    def on_fault(self, error_message: str):
        pass
