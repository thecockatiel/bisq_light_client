import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from contextvars import ContextVar
from typing import Optional
from contextlib import contextmanager

from bisq.common.util.utilities import get_sys_info
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from utils.preconditions import check_argument

DEFAULT_LOG_LEVEL = logging.INFO

ctx = ContextVar[Optional[logging.Logger]]("logger", default=None)


def get_ctx_logger(name: str):
    logger = ctx.get()
    if not logger:
        raise IllegalStateException("context is expected to contain a logger")
    return logger.getChild(name)


@contextmanager
def logger_context(value: logging.Logger):
    token = ctx.set(value)
    try:
        yield
    finally:
        ctx.reset(token)


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

abbreviate_pattern = re.compile(r"\b(\w+)(?=\.\w+)")


def abbreviate_dotted_words(words: str):
    return abbreviate_pattern.sub(lambda m: m.group(1)[0], words)


allowed_user_id_loggers = set[str]()


class BisqLogger(logging.Logger):
    def getChild(self, name: str):
        if self.name.startswith("user_"):
            uid = self.name[5:13]  # userid is 8 char long
            if uid not in allowed_user_id_loggers:
                raise IllegalStateException(
                    f"user_id `{uid}` is not allowed to make child loggers at this point"
                )

        return super().getChild(abbreviate_dotted_words(name))


logging.setLoggerClass(BisqLogger)

# Create formatter with pattern matching Java configuration
formatter = logging.Formatter(
    fmt="%(asctime)s [%(threadName)s] %(levelname)-5s %(name)-15s: %(message)s",
    datefmt="%b-%d %H:%M:%S",
)

_rolling_ext_re = re.compile(r"^\.(\d+)+$")

stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(DEFAULT_LOG_LEVEL)

base_logger = logging.getLogger("global")
base_logger.propagate = False
base_logger.addHandler(stdout_handler)
base_logger.setLevel(DEFAULT_LOG_LEVEL)
base_logger_file_handler = None
shared_logger = base_logger.getChild("shared")
shared_logger.propagate = False
shared_logger.addHandler(stdout_handler)


def get_base_logger(name: str):
    return base_logger.getChild(name)


def get_shared_logger(name: str) -> logging.Logger:
    return shared_logger.getChild(name)


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


def setup_aggregated_logger(app_data_dir: Path, log_level="INFO"):
    global base_logger_file_handler
    log_dir = app_data_dir.joinpath("all_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = str(log_dir.joinpath("bisq.log"))
    file_handler = CustomRotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=20,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    base_logger_file_handler = file_handler
    base_logger.addHandler(file_handler)
    shared_logger.addHandler(file_handler)

    base_logger.info(f"Aggregated log file at: {log_file}")
    base_logger.info(get_sys_info())


user_loggers: dict[str, logging.Logger] = {}
user_file_handlers: dict[str, CustomRotatingFileHandler] = {}


def get_user_log_file_path(user_data_dir: Path):
    return str(user_data_dir.joinpath("bisq.log"))


def get_user_logger(user_id: str, user_data_dir: Path, log_level="INFO"):
    if user_id in user_loggers:
        return user_loggers[user_id]

    allowed_user_id_loggers.add(user_id)

    log_level = getattr(logging, log_level.upper(), DEFAULT_LOG_LEVEL)

    user_loggers[user_id] = user_logger = logging.getLogger(f"user_{user_id}")
    user_logger.setLevel(log_level)
    user_logger.propagate = False

    # add file handler
    log_file = get_user_log_file_path(user_data_dir)

    file_handler = CustomRotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=20,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    user_logger.addHandler(file_handler)
    if base_logger_file_handler:
        user_logger.addHandler(
            base_logger_file_handler
        )  # we want each user logger to log to the aggregated logger as well.

    # Set specific logger levels
    user_logger.getChild("utils.tor").setLevel(logging.WARN)

    # we want shared logger logs to be logged in each user log files
    # but not base logger
    # so we keep the reference and add it to shared_logger handlers when we start the instance
    user_file_handlers[user_id] = file_handler

    return user_logger


def add_user_handler_to_shared(user_id: str):
    if user_id not in user_file_handlers:
        raise IllegalStateException(f"User `{user_id}` logger not initialized yet")
    shared_logger.removeHandler(user_file_handlers[user_id])


def remove_user_handler_from_shared(user_id: str, del_handler=False):
    handler = user_file_handlers.get(user_id, None)
    if handler:
        shared_logger.removeHandler(handler)
        if del_handler:
            del user_file_handlers[user_id]


_current_user_logger: logging.Logger = None


def switch_std_handler_to(user_id: str):
    global _current_user_logger
    check_argument(user_id in user_loggers, "user logger not initialized yet")
    if _current_user_logger is not None:
        _current_user_logger.removeHandler(stdout_handler)
    _current_user_logger = user_loggers[user_id]
    _current_user_logger.addHandler(stdout_handler)


def setup_log_for_test(test_name: str, data_dir: Path):
    user_logger = get_user_logger(test_name, data_dir, "TRACE")
    switch_std_handler_to(test_name)
    return user_logger


def destory_user_logger(user_id: str):
    global _current_user_logger
    allowed_user_id_loggers.discard(
        user_id
    )  # disallows creating new loggers for this user, just in case
    remove_user_handler_from_shared(user_id, True)
    if user_id in _current_user_logger.name:
        _current_user_logger.removeHandler(stdout_handler)
        _current_user_logger = None
    if user_id in user_loggers:
        logger = user_loggers[user_id]
        del user_loggers[user_id]
        # remove handlers
        for handler in logger.handlers.copy():
            logger.removeHandler(handler)
            handler.close()
        # release logger instances
        logger_dict = logger.manager.loggerDict
        to_remove = []
        for name in logger_dict:
            if name.startswith(f"user_{user_id}"):
                to_remove.append(name)
        for name in to_remove:
            del logger_dict[name]
        del to_remove
        del logger
