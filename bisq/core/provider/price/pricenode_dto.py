from typing_extensions import TypedDict


# the json data structure retrieved from the pricenode query
class PricenodeDto(TypedDict):
    data: list["PriceInfo"]
    bitcoinFeesTs: int
    bitcoinFeeInfo: "FeeInfo"
    
    class PriceInfo(TypedDict):
        currencyCode: str
        price: float
        timestampSec: int
        provider: str
        
    class FeeInfo(TypedDict):
        btcTxFee: int
        btcMinTxFee: int
        
