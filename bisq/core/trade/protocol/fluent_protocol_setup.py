from typing import TYPE_CHECKING, Optional, Type, TypeVar

if TYPE_CHECKING:
    from bisq.core.trade.protocol.fluent_protocol_event import FluentProtocolEvent
    from bisq.core.trade.protocol.trade_message import TradeMessage
    from bisq.core.trade.protocol.trade_task_runner import TradeTaskRunner
    from bisq.common.taskrunner.task import Task
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.trade.protocol.trade_protocol import TradeProtocol

_T = TypeVar("_T", bound="TradeModel")

class FluentProtocolSetup:
    def __init__(self, trade_protocol: 'TradeProtocol', trade_model: 'TradeModel'):
        self.trade_protocol = trade_protocol
        self.trade_model = trade_model
        self.tasks: list[Type['Task[_T]']] = []
        self.timeout_sec: int = 0
        self.task_runner: Optional['TradeTaskRunner'] = None

    def with_tasks(self, *task_classes: Type['Task[_T]']) -> 'FluentProtocolSetup':
        self.tasks = list(task_classes)
        return self

    def with_timeout(self, timeout_sec: int) -> 'FluentProtocolSetup':
        self.timeout_sec = timeout_sec
        return self

    def using(self, task_runner: 'TradeTaskRunner') -> 'FluentProtocolSetup':
        self.task_runner = task_runner
        return self

    def get_task_runner(self, message: Optional['TradeMessage'] = None, event: Optional['FluentProtocolEvent'] = None) -> 'TradeTaskRunner':
        if self.task_runner is None:
            if message is not None:
                self.task_runner = TradeTaskRunner(
                    self.trade_model,
                    lambda: self.trade_protocol.handle_task_runner_success(message),
                    lambda error_message: self.trade_protocol.handle_task_runner_fault(message, error_message)
                )
            elif event is not None:
                self.task_runner = TradeTaskRunner(
                    self.trade_model,
                    lambda: self.trade_protocol.handle_task_runner_success(event),
                    lambda error_message: self.trade_protocol.handle_task_runner_fault(event, error_message)
                )
            else:
                raise RuntimeError(
                    "addTasks must not be called without message or event set in case no taskRunner has been created yet"
                )
        return self.task_runner
