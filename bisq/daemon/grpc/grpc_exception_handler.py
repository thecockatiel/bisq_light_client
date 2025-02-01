from logging import Logger
from bisq.core.api.exception.already_exists_exception import AlreadyExistsException
from bisq.core.api.exception.failed_precondition_exception import (
    FailedPreconditionException,
)
from bisq.core.api.exception.not_available_exception import NotAvailableException
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.exceptions.unsupported_operation_exception import (
    UnsupportedOperationException,
)
from grpc import StatusCode, Status, ServicerContext

class GrpcStatus(Status):

    def __init__(self, code: "StatusCode", details: str, trailing_metadata=None):
        self.code = code
        self.details = details
        self.trailing_metadata = None


class GrpcExceptionHandler:
    """
    handles any expected core api Throwable by setting the right status and message for the gRPC response.
    An unexpected Throwable's message will be replaced with an 'unexpected' error message.

    works just a little different from java version's GrpcExceptionHandler
    """

    CORE_API_EXCEPTION_PKG_NAME = NotFoundException.__module__.rsplit(".", 1)[0]

    @staticmethod
    def _is_expected_exception(exception: Exception) -> bool:
        return exception.__class__.__module__.startswith(
            GrpcExceptionHandler.CORE_API_EXCEPTION_PKG_NAME
        ) or isinstance(
            exception,
            (
                IllegalArgumentException,
                IllegalStateException,
                UnsupportedOperationException,
            ),
        )

    @staticmethod
    def handle_exception(
        logger: Logger, exception: Exception, context: "ServicerContext"
    ):
        # Log the core api error (this is last chance to do that), wrap it in a new
        # gRPC StatusRuntimeException, then send it to the client in the gRPC response.
        logger.error("", exc_info=exception)
        grpc_status = GrpcExceptionHandler._wrap_exception(exception)
        context.abort(grpc_status.code, grpc_status.details)

    @staticmethod
    def handle_exception_as_warning(
        logger: Logger, called_method: str, exception: Exception, context: "ServicerContext"
    ):
        # Just log a warning instead of an error with full stack trace.
        logger.warning(f"{called_method} -> {str(exception)}")
        grpc_status = GrpcExceptionHandler._wrap_exception(exception)
        context.abort(grpc_status.code, grpc_status.details)

    @staticmethod
    def handle_error_message(logger: Logger, error_message: str, context: "ServicerContext"):
        # This is used to wrap Task errors from the ErrorMessageHandler
        # interface, an interface that is not allowed to throw exceptions.
        logger.error(error_message)
        grpc_status = GrpcStatus(
            StatusCode.UNKNOWN,
            GrpcExceptionHandler._cli_style_error_message(error_message),
        )
        context.abort(grpc_status.code, grpc_status.details)

    @staticmethod
    def _wrap_exception(exception: Exception):
        # We want to be careful about what kinds of exception messages we send to the
        # client.  Expected core exceptions should be wrapped in an IllegalStateException
        # or IllegalArgumentException, with a consistently styled and worded error
        # message.  But only a small number of the expected error types are currently
        # handled this way;  there is much work to do to handle the variety of errors
        # that can occur in the api.  In the meantime, we take care to not pass full,
        # unexpected error messages to the client.  If the exception type is unexpected,
        # we omit details from the gRPC exception sent to the client.
        if GrpcExceptionHandler._is_expected_exception(exception):
            if exception.__cause__:
                return GrpcExceptionHandler._map_grpc_error_status(
                    exception.__cause__, str(exception.__cause__)
                )
            return GrpcExceptionHandler._map_grpc_error_status(
                exception, str(exception)
            )
        return GrpcExceptionHandler._map_grpc_error_status(
            exception, "unexpected error on server"
        )

    @staticmethod
    def _cli_style_error_message(error_message: str) -> str:
        lines = error_message.replace("\r", "").split("\n")
        return lines[-1].lower()

    @staticmethod
    def _map_grpc_error_status(exception: Exception, description: str):
        # Check if a custom core.api.exception was thrown, so we can map it to a more
        # meaningful io.grpc.Status, something more useful to gRPC clients than UNKNOWN.
        # Core API specific exceptions
        if isinstance(exception, AlreadyExistsException):
            return GrpcStatus(StatusCode.ALREADY_EXISTS, description)
        elif isinstance(exception, FailedPreconditionException):
            return GrpcStatus(StatusCode.FAILED_PRECONDITION, description)
        elif isinstance(exception, NotFoundException):
            return GrpcStatus(StatusCode.NOT_FOUND, description)
        elif isinstance(exception, NotAvailableException):
            return GrpcStatus(StatusCode.UNAVAILABLE, description)

        # Standard exceptions
        if isinstance(exception, IllegalArgumentException):
            return GrpcStatus(StatusCode.INVALID_ARGUMENT, description)
        elif isinstance(exception, IllegalStateException):
            return GrpcStatus(StatusCode.UNKNOWN, description)
        elif isinstance(exception, UnsupportedOperationException):
            return GrpcStatus(StatusCode.UNIMPLEMENTED, description)

        return GrpcStatus(StatusCode.UNKNOWN, description)
