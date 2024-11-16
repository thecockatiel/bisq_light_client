from enum import IntEnum

# We can define here special features the client is supporting.
# Useful for updates to new versions where a new data type would break backwards compatibility or to
# limit a node to certain behaviour and roles like the seed nodes.
# We don't use the Enum in any serialized data, as changes in the enum would break backwards compatibility.
# We use the ordinal integer instead.
# Sequence in the enum must not be changed (append only).

class Capability(IntEnum):
    TRADE_STATISTICS = 0
    "@Deprecated TRADE_STATISTICS: Not required anymore as no old clients out there not having that support"

    TRADE_STATISTICS_2 = 1
    "@Deprecated TRADE_STATISTICS_2: Not required anymore as no old clients out there not having that support"

    ACCOUNT_AGE_WITNESS = 2
    "@Deprecated ACCOUNT_AGE_WITNESS: Not required anymore as no old clients out there not having that support"

    SEED_NODE = 3 
    "Node is a seed node"

    DAO_FULL_NODE = 4  
    "DAO full node can deliver BSQ blocks"

    PROPOSAL = 5
    "@Deprecated PROPOSAL: Not required anymore as no old clients out there not having that support"

    BLIND_VOTE = 6
    "@Deprecated BLIND_VOTE: Not required anymore as no old clients out there not having that support"

    ACK_MSG = 7
    "@Deprecated ACK_MSG: Not required anymore as no old clients out there not having that support"

    RECEIVE_BSQ_BLOCK = 8  
    "Signaling that node which wants to receive BSQ blocks (DAO lite node)"

    DAO_STATE = 9
    "@Deprecated DAO_STATE: Not required anymore as no old clients out there not having that support"

    BUNDLE_OF_ENVELOPES = 10
    "@Deprecated BUNDLE_OF_ENVELOPES: Supports bundling of messages if many messages are sent in short interval"

    SIGNED_ACCOUNT_AGE_WITNESS = 11
    "Supports the signed account age witness feature"

    MEDIATION = 12
    "Supports mediation feature"

    REFUND_AGENT = 13
    "Supports refund agents"

    TRADE_STATISTICS_HASH_UPDATE = 14
    "We changed the hash method in 1.2.0 and that requires update to 1.2.2 for handling it correctly, otherwise the seed nodes have to process too much data."

    NO_ADDRESS_PRE_FIX = 15
    "At 1.4.0 we removed the prefix filter for mailbox messages. If a peer has that capability we do not send the prefix."

    TRADE_STATISTICS_3 = 16
    "We used a new reduced trade statistics model from v1.4.0 on"

    BSQ_SWAP_OFFER = 17
    "Supports new message type BsqSwapOffer"
