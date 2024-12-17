from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.trade.protocol.fluent_protocol_condition_result import FluentProtocolConditionResult
from bisq.core.util.validator import Validator

if TYPE_CHECKING:
    from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.trade.model.trade_phase import TradePhase
    from bisq.core.trade.model.trade_state import TradeState
    from bisq.core.network.p2p.node_address import NodeAddress


logger = get_logger(__name__)

class FluentProtocolCondition:
    
    def __init__(self, trade_model: "TradeModel"):
        self.trade_model = trade_model
        
        self.expected_phases = set["TradePhase"]()
        self.expected_states = set["TradeState"]()
        self.pre_conditions = set["bool"]()
        self.result: Optional["FluentProtocolConditionResult"] = None
        
        self.message: Optional["TradeMessage"] = None
        self.event: Optional["FluentProtocolEvent"] = None
        self.peer: Optional["NodeAddress"] = None
        self.pre_conditions_failed_handler: Optional[Callable[[], None]] = None
        
    def add_phase(self, phase: "TradePhase") -> "FluentProtocolCondition":
        assert self.result is None
        self.expected_phases.add(phase)
        return self
        
    def add_phases(self, *phases: "TradePhase") -> "FluentProtocolCondition":
        assert self.result is None
        self.expected_phases.update(phases)
        return self
        
    def add_state(self, state: "TradeState") -> "FluentProtocolCondition":
        assert self.result is None
        self.expected_states.add(state)
        return self
        
    def add_states(self, *states: "TradeState") -> "FluentProtocolCondition":
        assert self.result is None
        self.expected_states.update(states)
        return self
        
    def with_message(self, message: "TradeMessage") -> "FluentProtocolCondition":
        assert self.result is None
        self.message = message
        return self
        
    def with_event(self, event: "FluentProtocolEvent") -> "FluentProtocolCondition":
        assert self.result is None
        self.event = event
        return self
        
    def from_peer(self, peer: "NodeAddress") -> "FluentProtocolCondition":
        assert self.result is None
        self.peer = peer
        return self
        
    def add_precondition(self, precondition: bool, condition_failed_handler: Optional[Callable[[], None]] = None) -> "FluentProtocolCondition":
        assert self.result is None
        self.pre_conditions.add(precondition)
        if condition_failed_handler is not None:
            self.pre_conditions_failed_handler = condition_failed_handler
        return self

    def get_result(self) -> "FluentProtocolConditionResult":
        if self.result is None:
            is_trade_id_valid = self.message is None or Validator.is_trade_id_valid(self.trade_model.get_id(), self.message)
            if not is_trade_id_valid:
                info = f"TradeId does not match tradeId in message, TradeId={self.trade_model.get_id()}, tradeId in message={self.message.trade_id}"
                self.result = FluentProtocolConditionResult.INVALID_TRADE_ID.with_info(info)
                return self.result

            phase_validation_result = self.get_phase_result()
            if not phase_validation_result.is_valid:
                self.result = phase_validation_result
                return self.result

            state_result = self.get_state_result()
            if not state_result.is_valid:
                self.result = state_result
                return self.result

            all_pre_conditions_met = all(self.pre_conditions)
            if not all_pre_conditions_met:
                info = f"PreConditions not met. preConditions={self.pre_conditions}, this={self}, tradeId={self.trade_model.id}"
                self.result = FluentProtocolConditionResult.INVALID_PRE_CONDITION.info(info)

                if self.pre_conditions_failed_handler is not None:
                    self.pre_conditions_failed_handler()
                return self.result

            self.result = FluentProtocolConditionResult.VALID

        return self.result

    def get_phase_result(self) -> "FluentProtocolConditionResult":
        if not self.expected_phases:
            return FluentProtocolConditionResult.VALID

        is_phase_valid = any(phase == self.trade_model.get_trade_phase() for phase in self.expected_phases)
        trigger = (self.message.__class__.__name__ if self.message is not None
                  else f"{self.event.name} event" if self.event is not None
                  else "")

        if is_phase_valid:
            info = f"We received a {trigger} at phase {self.trade_model.get_trade_phase()} and state {self.trade_model.get_trade_state()}, tradeId={self.trade_model.get_id()}"
            logger.info(info)
            return FluentProtocolConditionResult.VALID.info(info)
        else:
            info = (f"We received a {trigger} but we are are not in the expected phase.\n"
                   f"This can be an expected case if we get a repeated CounterCurrencyTransferStartedMessage "
                   f"after we have already received one as the peer re-sends that message at each startup.\n"
                   f"Expected phases={self.expected_phases},\nTrade phase={self.trade_model.get_trade_phase()},"
                   f"\nTrade state={self.trade_model.get_trade_state()},\ntradeId={self.trade_model.get_id()}")
            return FluentProtocolConditionResult.INVALID_PHASE.info(info)

    def get_state_result(self) -> "FluentProtocolConditionResult":
        if not self.expected_states:
            return FluentProtocolConditionResult.VALID

        is_state_valid = any(state == self.trade_model.get_trade_state() for state in self.expected_states)
        trigger = (self.message.__class__.__name__ if self.message is not None
                  else f"{self.event.name} event" if self.event is not None
                  else "")

        if is_state_valid:
            info = f"We received a {trigger} at state {self.trade_model.get_trade_state()}, tradeId={self.trade_model.get_id()}"
            logger.info(info)
            return FluentProtocolConditionResult.VALID.info(info)
        else:
            info = (f"We received a {trigger} but we are are not in the expected state. "
                   f"Expected states={self.expected_states}, Trade state={self.trade_model.get_trade_state()}, "
                   f"tradeId={self.trade_model.get_id()}")
            return FluentProtocolConditionResult.INVALID_STATE.info(info)