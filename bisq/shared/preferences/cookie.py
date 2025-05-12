from typing import Optional
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.shared.preferences.cookie_key import CookieKey

class Cookie(dict[CookieKey, str]):
    """
    Serves as flexible container for persisting UI states, layout,...
    Should not be over-used for domain specific data where type safety and data integrity is important.
    """
    
    def put_as_float(self, key: CookieKey, value: float) -> None:
        self[key] = str(value)
        
    def get_as_optional_float(self, key: CookieKey) -> Optional[float]:
        try:
            return float(self[key]) if key in self else None
        except (ValueError, KeyError):
            return None
            
    def put_as_boolean(self, key: CookieKey, value: bool) -> None:
        self[key] = "1" if value else "0"
        
    def get_as_optional_boolean(self, key: CookieKey) -> Optional[bool]:
        return self.get(key) == "1" if key in self else None
        
    def to_proto_message(self) -> dict[str, str]:
        return {key.name: value for key, value in self.items() if key is not None}
    
    @staticmethod
    def from_proto(proto_map: Optional[dict[str, str]] = None) -> 'Cookie':
        cookie = Cookie()
        if proto_map is not None:
            for key, value in proto_map.items():
                cookie[CookieKey.from_proto(key)] = value
        return cookie
