# TODO: Implemented partially since it was used widely, to complete later as needed.
from typing import TYPE_CHECKING
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.log_setup import get_logger
from resources import get_resources_path
from utils.java_compat import parse_resource_bundle

if TYPE_CHECKING:
    from bisq.common.config.config import Config

logger = get_logger(__name__)


class Res:
    _already_set_up = False
    base_currency_code: str = None
    base_currency_name: str = None
    base_currency_name_lower_case: str = None
    resources = dict[str, str]()

    @staticmethod
    def setup(config: "Config"):
        if Res._already_set_up:
            return
        Res._already_set_up = True
        base_currency_network = config.base_currency_network
        Res.set_base_currency_code(base_currency_network.currency_code)
        Res.set_base_currency_name(base_currency_network.currency_name)
        i18n_dir = get_resources_path().joinpath("i18n")
        for file in i18n_dir.glob("*.properties"):
            parsed = parse_resource_bundle(file)
            if parsed:
                Res.resources.update(parse_resource_bundle(file))

    @staticmethod
    def set_base_currency_code(base_currency_code: str):
        Res.base_currency_code = base_currency_code

    @staticmethod
    def set_base_currency_name(base_currency_name: str):
        Res.base_currency_name = base_currency_name
        Res.base_currency_name_lower_case = base_currency_name.lower()

    @staticmethod
    def get(key: str, *args):
        # only format if args are provided
        try:
            message = (
                Res.resources[key]
                .replace("BTC", Res.base_currency_code)
                .replace("Bitcoin", Res.base_currency_name)
                .replace("bitcoin", Res.base_currency_name_lower_case)
            )
        except KeyError:
            message = key
            logger.warning(f"Missing resource for key: {key}")

        if args:
            return message.format(*args)
        return message

    @staticmethod
    def get_with_col(key: str, *args):
        return Res.resources.get(key, key).format(*args) + ":"
