import os
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.resources import core_resource_readlines

logger = get_logger(__name__)


class CoreHelpService:

    def get_method_help(self, method_name: str):
        if not method_name:
            raise IllegalArgumentException("method name is required")

        resource_file = os.path.join("help", f"{method_name}-help.txt")
        try:
            lines = core_resource_readlines(resource_file)
            if not lines:
                raise IOError("File not found")
            return "".join(lines)
        except IOError as e:
            logger.error("", exc_info=e)
            raise IllegalStateException(f"could not read {method_name} help doc")
        except Exception as e:
            logger.error("", exc_info=e)
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
