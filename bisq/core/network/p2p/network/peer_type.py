from enum import IntEnum

class PeerType(IntEnum):
    # PEER is default type
    PEER = 0
    # If connection was used for initial data request/response. Those are marked with the InitialDataExchangeMessage interface
    INITIAL_DATA_EXCHANGE = 1
    # If a PrefixedSealedAndSignedMessage was sent (usually a trade message). Expects that node address is known.
    DIRECT_MSG_PEER = 2