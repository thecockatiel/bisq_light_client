
import logging

# TODO: setup proper logging.

electrum_logger = logging.getLogger("bisq_light")
electrum_logger.setLevel(logging.DEBUG)

def get_logger(name: str) -> logging.Logger:
    if name.startswith("bisq_light."):
        name = name[11:]
    return electrum_logger.getChild(name)

_logger = get_logger(__name__)
_logger.setLevel(logging.INFO)

def configure_logging():
    pass