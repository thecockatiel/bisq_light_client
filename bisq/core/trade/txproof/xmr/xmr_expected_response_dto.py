from typing import TYPE_CHECKING, TypedDict, cast

class XmrExpectedResponseDto(TypedDict):
    status: str
    data: "DataDict"
    
    class DataDict(TypedDict):
        address: str
        tx_hash: str
        viewkey: str
        tx_timestamp: int
        tx_confirmations: int
        outputs: list["OutputDict"]
        
        class OutputDict(TypedDict):
            amount: int
            match: bool
