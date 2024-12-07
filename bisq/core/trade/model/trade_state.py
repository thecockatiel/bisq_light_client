from enum import Enum
from bisq.core.trade.model.trade_state_protocol import TradeStateProtocol
import proto.pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.trade.model.trade_phase import TradePhase

class TradeState(TradeStateProtocol, Enum):
    # #################### Phase PREPARATION
    # When trade protocol starts no funds are on stake
    PREPARATION = TradePhase.INIT
    
    # At first part maker/taker have different roles
    # taker perspective
    # #################### Phase TAKER_FEE_PUBLISHED
    TAKER_PUBLISHED_TAKER_FEE_TX = TradePhase.TAKER_FEE_PUBLISHED
    
    # PUBLISH_DEPOSIT_TX_REQUEST
    # maker perspective
    MAKER_SENT_PUBLISH_DEPOSIT_TX_REQUEST = TradePhase.TAKER_FEE_PUBLISHED
    MAKER_SAW_ARRIVED_PUBLISH_DEPOSIT_TX_REQUEST = TradePhase.TAKER_FEE_PUBLISHED
    MAKER_STORED_IN_MAILBOX_PUBLISH_DEPOSIT_TX_REQUEST = TradePhase.TAKER_FEE_PUBLISHED  # not a mailbox msg, not used...
    MAKER_SEND_FAILED_PUBLISH_DEPOSIT_TX_REQUEST = TradePhase.TAKER_FEE_PUBLISHED
    
    # taker perspective
    TAKER_RECEIVED_PUBLISH_DEPOSIT_TX_REQUEST = TradePhase.TAKER_FEE_PUBLISHED  # Not used anymore
    
    # #################### Phase DEPOSIT_PUBLISHED
    # We changes order in trade protocol of publishing deposit tx and sending it to the peer.
    # Now we send it first to the peer and only if that succeeds we publish it to avoid likelihood of
    # failed trades. We do not want to change the order of the enum though so we keep it here as it was originally.
    SELLER_PUBLISHED_DEPOSIT_TX = TradePhase.DEPOSIT_PUBLISHED
    
    # DEPOSIT_TX_PUBLISHED_MSG
    # seller perspective
    SELLER_SENT_DEPOSIT_TX_PUBLISHED_MSG = TradePhase.DEPOSIT_PUBLISHED # Deprecated
    SELLER_SAW_ARRIVED_DEPOSIT_TX_PUBLISHED_MSG = TradePhase.DEPOSIT_PUBLISHED # Deprecated
    SELLER_STORED_IN_MAILBOX_DEPOSIT_TX_PUBLISHED_MSG = TradePhase.DEPOSIT_PUBLISHED # Deprecated
    SELLER_SEND_FAILED_DEPOSIT_TX_PUBLISHED_MSG = TradePhase.DEPOSIT_PUBLISHED # Deprecated
    
    # buyer perspective
    BUYER_RECEIVED_DEPOSIT_TX_PUBLISHED_MSG = TradePhase.DEPOSIT_PUBLISHED
    
    # Alternatively the buyer could have seen the deposit tx earlier before he received the DEPOSIT_TX_PUBLISHED_MSG
    BUYER_SAW_DEPOSIT_TX_IN_NETWORK = TradePhase.DEPOSIT_PUBLISHED
    
    # #################### Phase DEPOSIT_CONFIRMED
    DEPOSIT_CONFIRMED_IN_BLOCK_CHAIN = TradePhase.DEPOSIT_CONFIRMED
    
    # #################### Phase FIAT_SENT
    BUYER_CONFIRMED_IN_UI_FIAT_PAYMENT_INITIATED = TradePhase.FIAT_SENT
    BUYER_SENT_FIAT_PAYMENT_INITIATED_MSG = TradePhase.FIAT_SENT
    BUYER_SAW_ARRIVED_FIAT_PAYMENT_INITIATED_MSG = TradePhase.FIAT_SENT
    BUYER_STORED_IN_MAILBOX_FIAT_PAYMENT_INITIATED_MSG = TradePhase.FIAT_SENT
    BUYER_SEND_FAILED_FIAT_PAYMENT_INITIATED_MSG = TradePhase.FIAT_SENT
    
    SELLER_RECEIVED_FIAT_PAYMENT_INITIATED_MSG = TradePhase.FIAT_SENT
    
    # #################### Phase FIAT_RECEIVED
    # note that this state can also be triggered by auto confirmation feature
    SELLER_CONFIRMED_IN_UI_FIAT_PAYMENT_RECEIPT = TradePhase.FIAT_RECEIVED
    
    # #################### Phase PAYOUT_PUBLISHED
    SELLER_PUBLISHED_PAYOUT_TX = TradePhase.PAYOUT_PUBLISHED
    
    SELLER_SENT_PAYOUT_TX_PUBLISHED_MSG = TradePhase.PAYOUT_PUBLISHED
    SELLER_SAW_ARRIVED_PAYOUT_TX_PUBLISHED_MSG = TradePhase.PAYOUT_PUBLISHED
    SELLER_STORED_IN_MAILBOX_PAYOUT_TX_PUBLISHED_MSG = TradePhase.PAYOUT_PUBLISHED
    SELLER_SEND_FAILED_PAYOUT_TX_PUBLISHED_MSG = TradePhase.PAYOUT_PUBLISHED
    
    BUYER_RECEIVED_PAYOUT_TX_PUBLISHED_MSG = TradePhase.PAYOUT_PUBLISHED
    # Alternatively the maker could have seen the payout tx earlier before he received the PAYOUT_TX_PUBLISHED_MSG
    BUYER_SAW_PAYOUT_TX_IN_NETWORK = TradePhase.PAYOUT_PUBLISHED
    
    # #################### Phase WITHDRAWN
    WITHDRAW_COMPLETED = TradePhase.WITHDRAWN
    
    def __init__(self, phase: "TradePhase"):
        self.phase = phase

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
    
    @staticmethod
    def from_proto(proto: protobuf.Trade.State) -> "TradeState":
        return ProtoUtil.enum_from_proto(TradeState, protobuf.Trade.State, proto)

    @staticmethod
    def to_proto_message(state: "TradeState"):
        return ProtoUtil.proto_enum_from_enum(protobuf.Trade.State, state)
    
    # We allow a state change only if the phase is the next phase or if we do not change the phase by the
    # state change (e.g. detail change inside the same phase)
    def is_valid_transition_to(self, new_state: "TradeState"):
        new_phase = new_state.phase
        current_phase = self.phase
        return current_phase.is_valid_transition_to(new_phase) or new_phase == current_phase
