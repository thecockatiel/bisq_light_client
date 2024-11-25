from abc import ABC, abstractmethod
import secrets
from typing import Dict, Optional
import binascii
from bisq.common.setup.log_setup import get_logger
import proto.pb_pb2 as protobuf

from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.used_for_trade_contract_json import UsedForTradeContractJson

logger = get_logger(__name__)

# todo: double check impl
class PaymentAccountPayload(NetworkPayload, UsedForTradeContractJson, ABC):
    """
    That class is used in the contract for creating the contract json. Any change will break the contract.
    If a field gets added it need to be be annotated with @JsonExclude (excluded from contract).
    We should add an extraDataMap as in StoragePayload objects
    """
    
    # Keys for excludeFromJsonDataMap
    SALT = "salt"
    HOLDER_NAME = "holderName"

    def __init__(self, payment_method_id: str, id: str, 
                 max_trade_period: int = -1, 
                 exclude_from_json_data_map: Optional[Dict[str, str]] = None):
        """Constructor for PaymentAccountPayload"""
        self.payment_method_id = payment_method_id
        self.id = id
        # Is just kept for not breaking backward compatibility. Set to -1 to indicate it is no used anymore.
        # In v0.6 we removed maxTradePeriod but we need to keep it in the PB file for backward compatibility
        self.max_trade_period = max_trade_period
        # Used for new data (e.g. salt introduced in v0.6) which would break backward compatibility as
        # PaymentAccountPayload is used for the json contract and a trade with a user who has an older version would
        # fail the contract verification.
        self.exclude_from_json_data_map = exclude_from_json_data_map or {}

        # If not set (old versions) we set by default a random 256 bit salt
        # User can set salt as well by hex string.
        # Persisted value will overwrite that
        if self.SALT not in self.exclude_from_json_data_map:
            random_bytes = secrets.token_bytes(32)
            self.exclude_from_json_data_map[PaymentAccountPayload.SALT] = binascii.hexlify(random_bytes).decode()

    def get_payment_account_payload_builder(self):
        payload = protobuf.PaymentAccountPayload(
            payment_method_id=self.payment_method_id,
            max_trade_period=self.max_trade_period,
            id=self.id,
            exclude_from_json_data=self.exclude_from_json_data_map
        ) 
        return payload

    @abstractmethod
    def get_payment_details(self) -> str:
        pass

    @abstractmethod
    def get_payment_details_for_trade_popup(self) -> str:
        pass

    def show_ref_text_warning(self) -> bool:
        return True

    def get_salt(self) -> bytes:
        assert self.SALT in self.exclude_from_json_data_map, "Salt must have been set in exclude_from_json_data_map"
        return binascii.unhexlify(self.exclude_from_json_data_map[self.SALT])

    def set_salt(self, salt: bytes) -> None:
        self.exclude_from_json_data_map[self.SALT] = binascii.hexlify(salt).decode()

    def get_holder_name(self) -> str:
        return self.exclude_from_json_data_map.get(self.HOLDER_NAME, "")

    def get_holder_name_or_prompt_if_empty(self) -> str:
        return "payment.account.owner.ask" if self.get_holder_name() == "" else self.get_holder_name()

    def set_holder_name(self, holder_name: str) -> None:
        # an empty string must result in the mapping removing the entry.
        if holder_name:
            self.exclude_from_json_data_map[self.HOLDER_NAME] = holder_name
        elif self.HOLDER_NAME in self.exclude_from_json_data_map:
            del self.exclude_from_json_data_map[self.HOLDER_NAME]

    @abstractmethod
    def get_age_witness_input_data(self) -> bytes:
        """
        Identifying data of payment account (e.g. IBAN).
        This is critical code for verifying age of payment account.
        Any change would break validation of historical data!
        """
        pass
    
    def get_age_witness_input_data_with_bytes(self, data: bytes) -> bytes:
        return self.payment_method_id.encode('utf-8') + data

    def get_owner_id(self) -> Optional[str]:
        return None
    
    # NOTE: we need to handle this for java compatiblity because of FilterManager calling the methods dynamically and name coming over the wire
    
    def __getattr__(self, name: str):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            snake_case = ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')
            return object.__getattribute__(self, snake_case)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PaymentAccountPayload):
            return False
        return (self.payment_method_id == other.payment_method_id and
                self.id == other.id and
                self.max_trade_period == other.max_trade_period and
                self.exclude_from_json_data_map == other.exclude_from_json_data_map)

    def __str__(self) -> str:
        return (f"PaymentAccountPayload(payment_method_id={self.payment_method_id}, "
                f"id={self.id}, max_trade_period={self.max_trade_period}, "
                f"exclude_from_json_data_map={self.exclude_from_json_data_map})")