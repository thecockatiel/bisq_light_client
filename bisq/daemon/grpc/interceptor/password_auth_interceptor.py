from typing import TYPE_CHECKING, Callable
from grpc import (
    ServerInterceptor,
    StatusCode,
    ServicerContext,
    unary_unary_rpc_method_handler,
)


if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from utils.grpc_type_hints import HandlerCallDetails


def _unary_unary_rpc_terminator(code: StatusCode, details: str):
    def terminate(ignored_request, context: "ServicerContext"):
        context.abort(code, details)

    return unary_unary_rpc_method_handler(terminate)


class PasswordAuthInterceptor(ServerInterceptor):
    """
    Authorizes rpc server calls by comparing the value of the caller's
    PASSWORD_KEY header to an expected value set at server startup time.

    see Config#apiPassword
    """

    PASSWORD_KEY = "password"

    def __init__(self, config: "Config"):
        super().__init__()
        self.expected_password_value = config.api_password
        self._missing_password_terminator = _unary_unary_rpc_terminator(
            StatusCode.UNAUTHENTICATED,
            f"missing '{PasswordAuthInterceptor.PASSWORD_KEY}' rpc header",
        )
        self._wrong_password_terminator = _unary_unary_rpc_terminator(
            StatusCode.UNAUTHENTICATED,
            f"incorrect '{PasswordAuthInterceptor.PASSWORD_KEY}' rpc header",
        )

    def intercept_service(
        self, continuation: Callable, handler_call_details: "HandlerCallDetails"
    ) -> Callable:

        actual_password = next(
            (
                value
                for header, value in handler_call_details.invocation_metadata
                if header == PasswordAuthInterceptor.PASSWORD_KEY
            ),
            None,
        )

        if actual_password is None:
            return self._missing_password_terminator

        if actual_password != self.expected_password_value:
            return self._wrong_password_terminator

        return continuation(handler_call_details)
