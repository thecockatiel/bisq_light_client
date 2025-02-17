import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re

from bisq.common.util.utilities import get_sys_info

DEFAULT_LOG_LEVEL = logging.INFO


# https://stackoverflow.com/a/35804945
def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


addLoggingLevel("TRACE", logging.DEBUG - 5)

# Create formatter with pattern matching Java configuration
formatter = logging.Formatter(
    fmt="%(asctime)s [%(threadName)s] %(levelname)-5s %(name)-15s: %(message)s",
    datefmt="%b-%d %H:%M:%S",
)

bisq_logger = logging.getLogger("bisq_light")
# add basic logging to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(DEFAULT_LOG_LEVEL)
bisq_logger.addHandler(stdout_handler)


def get_logger(name: str) -> logging.Logger:
    if name.startswith("bisq_light."):
        name = name[11:]
    return bisq_logger.getChild(name)


_rolling_ext_re = re.compile(r"^\.(\d+)+$")


class CustomRotatingFileHandler(RotatingFileHandler):
    def rotation_filename(self, default_name):
        """Modify the rotation filename to generate name.count.ext instead of name.ext.count"""
        file_root, file_ext = os.path.splitext(default_name)
        if _rolling_ext_re.match(file_ext):
            rotation_num = file_ext.lstrip(".")
            file_root, file_ext = file_root.rsplit(".", 1)
        if rotation_num:
            return f"{file_root}_{rotation_num}.{file_ext}"
        return default_name


def configure_logging(log_file: Path, log_level="INFO"):
    log_level = getattr(logging, log_level.upper(), DEFAULT_LOG_LEVEL)

    # Create and configure rotating file handler with custom class
    if log_file:
        file_handler = CustomRotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=20,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        bisq_logger.addHandler(file_handler)

    bisq_logger.setLevel(log_level)
    for handler in bisq_logger.handlers:
        handler.setLevel(log_level)

    # Update child loggers' levels
    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith("bisq_light.") and isinstance(logger, logging.Logger):
            logger.setLevel(log_level)
            # update child loggers with root handlers
            logger.handlers = bisq_logger.handlers.copy()

    if log_file:
        bisq_logger.info(f"Log file at: {log_file}")
    bisq_logger.info(get_sys_info())

    # Set specific logger levels
    get_logger("utils.tor").setLevel(logging.WARN)


def set_custom_log_level(level):
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)
    bisq_logger.setLevel(level)
    for name, logger in logging.Logger.manager.loggerDict.items():
        if name.startswith("bisq_light.") and isinstance(logger, logging.Logger):
            logger.setLevel(level)
