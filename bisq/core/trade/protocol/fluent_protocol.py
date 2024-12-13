from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bisq.core.trade.protocol.fluent_protocol_condition import (
        FluentProtocolCondition,
    )
    from bisq.core.trade.protocol.fluent_protocol_condition_result import (
        FluentProtocolConditionResult,
    )
    from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent
    from bisq.core.trade.protocol.fluent_protocol_setup import FluentProtocolSetup
    from bisq.core.trade.protocol.trade_protocol import TradeProtocol


# Main class. Contains the condition and setup, if condition is valid it will execute the
# taskRunner and the optional runnable.
class FluentProtocol:

    def __init__(self, trade_protocol: "TradeProtocol"):
        self.trade_protocol = trade_protocol

        self.condition: Optional["FluentProtocolCondition"] = None
        self.setup: Optional["FluentProtocolSetup"] = None
        self.result_handler: Optional[
            Callable[["FluentProtocolConditionResult"], None]
        ] = None

    def with_condition(self, condition: "FluentProtocolCondition"):
        self.condition = condition
        return self

    def with_setup(self, setup: "FluentProtocolSetup"):
        self.setup = setup
        return self

    def with_result_handler(
        self, result_handler: Callable[["FluentProtocolConditionResult"], None]
    ):
        self.result_handler = result_handler
        return self

    # Can be used before or after executeTasks
    def run(self, runnable: Callable[[], None]) -> "FluentProtocol":
        result = self.condition.get_result()
        if result.is_valid:
            runnable()
        elif self.result_handler is not None:
            self.result_handler(result)
        return self

    def execute_tasks(self) -> "FluentProtocol":
        result = self.condition.get_result()
        if not result.is_valid:
            if self.result_handler is not None:
                self.result_handler(result)
            return self

        if self.setup.timeout_sec > 0:
            self.trade_protocol.start_timeout(self.setup.timeout_sec)

        peer = self.condition.peer
        if peer is not None:
            self.trade_protocol.protocol_model.temp_trading_peer_node_address = peer
            self.trade_protocol.protocol_model.trade_manager.request_persistence()

        message = self.condition.message
        if message is not None:
            self.trade_protocol.protocol_model.trade_message = message
            self.trade_protocol.protocol_model.trade_manager.request_persistence()

        task_runner = self.setup.get_task_runner(message, self.condition.event)
        task_runner.add_tasks(*self.setup.tasks)
        task_runner.run()
        return self