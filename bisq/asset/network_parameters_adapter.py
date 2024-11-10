

from bitcoinj.core.network_parameters import NetworkParameters


class NetworkParametersAdapter(NetworkParameters):
    
    def get_payment_protocol_id(self) -> str:
        return self.PAYMENT_PROTOCOL_ID_MAINNET
    
    def get_max_money(self):
        return None
    
    def get_min_non_dust_output(self):
        return None
    
    def get_monetary_format(self):
        return None
    
    def get_uri_scheme(self):
        return None
    
    def has_max_money(self):
        return None
    
    def get_serializer(self):
        return None
    
    def get_protocol_version_num(self):
        return 0