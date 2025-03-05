import logging
from typing import Optional

from bisq.common.setup.log_setup import get_logger as get_bisq_logger

def get_logger(name: str):
    logger = get_bisq_logger(name)
    # mute most of electrum logs
    logger.setLevel(logging.WARNING)
    return logger

class ShortcutInjectingFilter(logging.Filter):

    def __init__(self, *, shortcut: Optional[str]):
        super().__init__()
        self.__shortcut = shortcut

    def filter(self, record):
        record.custom_shortcut = self.__shortcut
        return True

class Logger:

    # Single character short "name" for this class.
    # Can be used for filtering log lines. Does not need to be unique.
    LOGGING_SHORTCUT = None  # type: Optional[str]

    def __init__(self):
        self.logger = self.__get_logger_for_obj()

    def __get_logger_for_obj(self) -> logging.Logger:
        cls = self.__class__
        if cls.__module__:
            name = f"{cls.__module__}.{cls.__name__}"
        else:
            name = cls.__name__
        try:
            diag_name = self.diagnostic_name()
        except Exception as e:
            raise Exception("diagnostic name not yet available?") from e
        if diag_name:
            name += f".[{diag_name}]"
        logger = get_logger(name)
        if self.LOGGING_SHORTCUT:
            logger.addFilter(ShortcutInjectingFilter(shortcut=self.LOGGING_SHORTCUT))
        return logger

    def diagnostic_name(self):
        return ''
