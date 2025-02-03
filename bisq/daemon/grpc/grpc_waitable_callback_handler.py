import threading
from typing import TYPE_CHECKING, Generic, Optional, TypeVar
from bisq.core.offer.availability.availability_result import AvailabilityResult
from grpc_pb2 import AvailabilityResultWithDescription
import pb_pb2

if TYPE_CHECKING:
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler

_T = TypeVar("_T")


# NOTE: This is Something like GrpcErrorMessageHandler of java,
# but with methods to be able to wait on the result or error
# and no special handling of errors inside.
class GrpcWaitableCallbackHandler(Generic[_T]):
    def __init__(self):
        self._result_container: dict[str, _T] = {"value": None}
        self._completion_event = threading.Event()
        self.has_errored = False
        self.error_message: Optional[str] = None

    def handle_result(self, result: _T = None, *args, **kwargs):
        if self._completion_event.is_set():
            return
        self._result_container["value"] = result
        self._completion_event.set()

    def handle_error_message(self, message: str, *args, **kwargs):
        # A task runner may call handleErrorMessage(String) more than once.
        # we capture only one the first one.
        if self.has_errored or self._completion_event.is_set():
            return
        self.has_errored = True
        self.error_message = message
        self._completion_event.set()

    def wait(self):
        self._completion_event.wait()
        return self._result_container["value"]

    def get_availability_result_with_description(
        self,
    ) -> Optional["AvailabilityResultWithDescription"]:
        """
        returns a grpc `AvailabilityResultWithDescription` if an error message was received and contains an `AvailabilityResult`.
        returns `None` otherwise.
        """
        if not self.error_message:
            return None
        proto = self._get_availability_result(self.error_message)
        description = self._get_availability_result_description(proto)
        return AvailabilityResultWithDescription(
            availability_result=proto, description=description
        )

    @staticmethod
    def _get_availability_result(error_message: str):
        for result in AvailabilityResult:
            if result.name in error_message.upper():
                return result
        raise ValueError(
            f"Could not find an AvailabilityResult in error message:\n{error_message}"
        )

    @staticmethod
    def _get_availability_result_description(proto: pb_pb2.AvailabilityResult):
        return AvailabilityResult.from_proto(proto).description
