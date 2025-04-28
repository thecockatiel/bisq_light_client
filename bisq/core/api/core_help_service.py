import os
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.user.user_manager import UserManager
from bisq.resources import core_resource_readlines


class CoreHelpService:

    def __init__(self, user_manager: "UserManager"):
        self._user_manager = user_manager

    def get_method_help(self, method_name: str):
        if not method_name:
            raise IllegalArgumentException("method name is required")

        user_context = self._user_manager.active_context

        resource_file = os.path.join("help", f"{method_name}-help.txt")
        try:
            lines = core_resource_readlines(resource_file)
            if not lines:
                raise IOError("File not found")
            return "".join(lines)
        except IOError as e:
            user_context.logger.error("", exc_info=e)
            raise IllegalStateException(f"could not read {method_name} help doc")
        except Exception as e:
            user_context.logger.error("", exc_info=e)
            raise NotFoundException(f"no help found for api method {method_name}")

    @staticmethod
    def main():
        # Main method for devs to view help text without running the server.
        coreHelpService = CoreHelpService()
        # print(coreHelpService.get_method_help("getversion"))
        # print(coreHelpService.get_method_help("getfundingaddresses"))
        # print(coreHelpService.get_method_help("getfundingaddresses"))
        # print(coreHelpService.get_method_help("getunusedbsqaddress"))
        # print(coreHelpService.get_method_help("unsettxfeerate"))
        # print(coreHelpService.get_method_help("getpaymentmethods"))
        # print(coreHelpService.get_method_help("getpaymentaccts"))
        # print(coreHelpService.get_method_help("lockwallet"))
        # print(coreHelpService.get_method_help("gettxfeerate"))
        # print(coreHelpService.get_method_help("createoffer"))
        # print(coreHelpService.get_method_help("takeoffer"))
        # print(coreHelpService.get_method_help("garbage"))
        print(coreHelpService.get_method_help(""))
        print(coreHelpService.get_method_help(None))
