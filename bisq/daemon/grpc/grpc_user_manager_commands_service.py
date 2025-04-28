from utils.aio import wait_future_blocking
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_base_logger
from grpc_extra_pb2_grpc import UserManagerCommandsServicer
from grpc_extra_pb2 import (
    RestoreUserReply,
    RestoreUserRequest,
    SetUserAliasReply,
    SetUserAliasRequest,
    SwitchUserRequest,
    SwitchUserReply,
    CreateNewUserRequest,
    CreateNewUserReply,
    DeleteUserRequest,
    DeleteUserReply,
    GetUsersListRequest,
    GetUsersListReply,
)

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi
    from bisq.core.user.user_manager import UserManager

base_logger = get_base_logger(__name__)


# TODO: recheck after adding core_api implementation


class GrpcUserManagerCommandsService(UserManagerCommandsServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self.core_api = core_api
        self.exception_handler = exception_handler
        self._user_manager = user_manager

    def SwitchUser(self, request: "SwitchUserRequest", context: "ServicerContext"):
        try:
            wait_future_blocking(self.core_api.switch_user(request.user_id))
            return SwitchUserReply()
        except Exception as e:
            self.exception_handler.handle_exception(base_logger, e, context)

    def CreateNewUser(
        self, request: "CreateNewUserRequest", context: "ServicerContext"
    ):
        try:
            user_id = wait_future_blocking(self.core_api.create_new_user())
            return CreateNewUserReply(user_id=user_id)
        except Exception as e:
            self.exception_handler.handle_exception(base_logger, e, context)

    def DeleteUser(self, request: "DeleteUserRequest", context: "ServicerContext"):
        try:
            new_user_id, created_new_user = wait_future_blocking(
                self.core_api.delete_user(request.user_id, request.delete_data)
            )
            return DeleteUserReply(new_user_id=new_user_id, created_new_user=created_new_user)
        except Exception as e:
            self.exception_handler.handle_exception(base_logger, e, context)

    def SetUserAlias(self, request: "SetUserAliasRequest", context: "ServicerContext"):
        try:
            self.core_api.set_user_alias(request.user_id, request.alias)
            return SetUserAliasReply()
        except Exception as e:
            self.exception_handler.handle_exception(base_logger, e, context)

    def GetUsersList(self, request: "GetUsersListRequest", context: "ServicerContext"):
        try:
            users_list = self.core_api.get_users_list()
            return GetUsersListReply(users_list=users_list)
        except Exception as e:
            self.exception_handler.handle_exception(base_logger, e, context)

    def RestoreUser(self, request: "RestoreUserRequest", context: "ServicerContext"):
        try:
            wait_future_blocking(self.core_api.restore_user(request.user_id))
            return RestoreUserReply()
        except Exception as e:
            self.exception_handler.handle_exception(base_logger, e, context)
