from enum import Enum

class CloseConnectionReason(Enum):
    # First block are from different exceptions
    SOCKET_CLOSED = False, False
    RESET = False, False
    SOCKET_TIMEOUT = False, False
    TERMINATED = False, False
    # EOFException
    CORRUPTED_DATA = False, False
    NO_PROTO_BUFFER_DATA = False, False
    NO_PROTO_BUFFER_ENV = False, False
    UNKNOWN_EXCEPTION = False, False

    # Planned
    APP_SHUT_DOWN = True, True
    CLOSE_REQUESTED_BY_PEER = False, True

    # send msg
    SEND_MSG_FAILURE = False, False
    SEND_MSG_TIMEOUT = False, False

    # maintenance
    TOO_MANY_CONNECTIONS_OPEN = True, True
    TOO_MANY_SEED_NODES_CONNECTED = True, True
    UNKNOWN_PEER_ADDRESS = True, True

    # illegal requests
    RULE_VIOLATION = True, False
    PEER_BANNED = False, False
    INVALID_CLASS_RECEIVED = False, False
    MANDATORY_CAPABILITIES_NOT_SUPPORTED = False, False

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    def __init__(self, send_close_message: bool, is_intended: bool):
        self.send_close_message = send_close_message
        self.is_intended = is_intended

    def __str__(self):
        return f"CloseConnectionReason{{sendCloseMessage={self.send_close_message}, isIntended={self.is_intended}}} {super().__str__()}"
