# TODO: Implemented partially since it was used widely, to complete later as needed.
from resources import get_resources_path
from utils.java_compat import parse_resource_bundle

class Res:
    base_currency_code: str = None
    base_currency_name: str = None
    base_currency_name_lower_case: str = None
    resources = dict[str, str]()
    
    @staticmethod
    def setup():
        from global_container import GLOBAL_CONTAINER
        base_currency_network = GLOBAL_CONTAINER.config.base_currency_network
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
        return Res.resources.get(key, key).format(*args)
    
    @staticmethod
    def get_with_col(key: str, *args):
        return Res.resources.get(key, key).format(*args) + ":"
    
Res.setup()
