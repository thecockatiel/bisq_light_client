
from abc import ABC

class UsedForTradeContractJson(ABC):
    """
    Marker interface for classes which are used in the trade contract.
    Any change of the class fields would breaking backward compatibility.
    If a field needs to get added it needs to be annotated with @JsonExclude (thus excluded from the contract JSON).
    Better to use the excludeFromJsonDataMap (annotated with @JsonExclude; used in PaymentAccountPayload) to
    add a key/value pair.
    """
    pass 
