
from abc import ABC
from typing import Optional

from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload 


class AssetsAccountPayload(PaymentAccountPayload, ABC):
    
    def __init__(self, payment_method_id: str, id: str, address: str = None, max_trade_period: int = -1, exclude_from_json_data_map: Optional[dict[str, str]] = None):
        super().__init__(payment_method_id, id, max_trade_period, exclude_from_json_data_map)
        self.address = address or ""
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_payment_details(self):
        return Res.get_with_col("payment.altcoin.receiver.address") + " " + self.address
    
    def get_payment_details_for_trade_popup(self):
        return self.get_payment_details()
    
    def show_ref_text_warning(self):
        return False
    
    def get_age_witness_input_data(self):
        return self.get_age_witness_input_data_using_bytes(self.address.encode('utf-8'))
