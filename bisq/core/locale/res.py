# TODO: Implemented partially since it was used widely, to complete later as needed.

class Res:
    base_currency_code: str = None
    base_currency_name: str = None
    base_currency_name_lower_case: str = None
    
    @staticmethod
    def setup():
        from global_container import GLOBAL_CONTAINER
        base_currency_network = GLOBAL_CONTAINER.config.base_currency_network
        Res.set_base_currency_code(base_currency_network.currency_code)
        Res.set_base_currency_name(base_currency_network.currency_name)
        
    @staticmethod
    def set_base_currency_code(base_currency_code: str):
        Res.base_currency_code = base_currency_code
    
    @staticmethod
    def set_base_currency_name(base_currency_name: str):
        Res.base_currency_name = base_currency_name
        Res.base_currency_name_lower_case = base_currency_name.lower()
    
    @staticmethod
    def get(key: str, *args):
        return key
    
    @staticmethod
    def get_with_col(key: str, *args):
        return Res.get(key) + ":"
    
Res.setup()