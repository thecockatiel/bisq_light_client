from typing import Optional
from bisq.asset.asset import Asset
from bisq.asset.coins.asset_registry import AssetRegistry
from bisq.common.app.dev_env import DevEnv
from bisq.core.locale.crypto_currency import CryptoCurrency
from bisq.core.locale.currency_data import (
    COUNTRY_TO_CURRENCY_CODE_MAP,
    CURRENCY_CODE_TO_DATA_MAP,
)
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency

# NOTE: ported from https://github.com/bisq-network/bisq/blob/release/v1.9.17/core/src/main/java/bisq/core/locale/CurrencyUtil.java

# TODO: not complete


def _asset_to_crypto_currency(asset: Asset):
    return CryptoCurrency(
        asset.get_ticker_symbol(), asset.get_name(), isinstance(asset, Asset)
    )

crypto_currency_map = {
    asset.get_ticker_symbol(): _asset_to_crypto_currency(asset)
    for asset in AssetRegistry.registered_assets
}

CURRENCY_CODE_TO_FIAT_CURRENCY_MAP = {
    currency_code: FiatCurrency(currency_data) for currency_code, currency_data in CURRENCY_CODE_TO_DATA_MAP.items()
}

def get_currency_by_country_code(country_code: str):
    currency_data = CURRENCY_CODE_TO_FIAT_CURRENCY_MAP[COUNTRY_TO_CURRENCY_CODE_MAP[country_code]]
    return currency_data

# along with the comments.
def is_crypto_currency(currency_code: str):
    """
    We return true if it is BTC or any of our currencies available in the assetRegistry.
    For removed assets it would fail as they are not found but we don't want to conclude that they are fiat then.
    As the caller might not deal with the case that a currency can be neither a cryptoCurrency nor Fiat if not found
    we return true as well in case we have no fiat currency for the code.

    As we use a boolean result for isCryptoCurrency and isFiatCurrency we do not treat missing currencies correctly.
    To throw an exception might be an option but that will require quite a lot of code change, so we don't do that
    for the moment, but could be considered for the future. Another maybe better option is to introduce an enum which
    contains 3 entries (CryptoCurrency, Fiat, Undefined).
    """
    if currency_code is None:
        # Some tests call that method with null values. Should be fixed in the tests but to not break them return false.
        return False
    elif currency_code == "BTC":
        # BTC is not part of our assetRegistry so treat it extra here. Other old base currencies (LTC, DOGE, DASH)
        # are not supported anymore so we can ignore that case.
        return True
    elif crypto_currency_map.get(currency_code):
        # If we find the code in our assetRegistry we return true.
        # It might be that an asset was removed from the assetsRegistry, we deal with such cases below by checking if
        # it is a fiat currency
        return True
    elif not CURRENCY_CODE_TO_DATA_MAP.get(currency_code, None):
        # In case the code is from a removed asset we cross check if there exist a fiat currency with that code,
        # if we don't find a fiat currency we treat it as a crypto currency.
        return True
    else:
        return False

def is_fiat_currency(currency_code: str):
    if (
        currency_code
        and not is_crypto_currency(currency_code)
        and currency_code in CURRENCY_CODE_TO_DATA_MAP
    ):
        return True
    return False

BASE_CURRENCY_CODE = "BTC"

def set_base_currency_code(currency_code: str):
    global BASE_CURRENCY_CODE
    BASE_CURRENCY_CODE = currency_code
    
def setup():
    from global_container import GLOBAL_CONTAINER
    set_base_currency_code(GLOBAL_CONTAINER.config.base_currency_network.currency_code)
    
MATURE_MARKET_CURRENCIES = tuple(sorted([
    FiatCurrency("EUR"),
    FiatCurrency("USD"), 
    FiatCurrency("GBP"),
    FiatCurrency("CAD"),
    FiatCurrency("AUD"),
    FiatCurrency("BRL")
], key=lambda x: x.code))

def get_mature_market_currencies():
    return MATURE_MARKET_CURRENCIES


SORTED_BY_NAME_FIAT_CURRENCIES = sorted(list(CURRENCY_CODE_TO_FIAT_CURRENCY_MAP.values()), key=lambda x: x.name)
SORTED_BY_CODE_FIAT_CURRENCIES = sorted(SORTED_BY_NAME_FIAT_CURRENCIES, key=lambda x: x.code)

def get_main_fiat_currencies() -> list["TradeCurrency"]:
    from bisq.core.locale.global_settings import GlobalSettings
    default_trade_currency = GlobalSettings.default_trade_currency
    currencies = list["FiatCurrency"]()
    # Top traded currencies
    currencies.append(FiatCurrency("USD"))
    currencies.append(FiatCurrency("EUR"))
    currencies.append(FiatCurrency("GBP"))
    currencies.append(FiatCurrency("CAD"))
    currencies.append(FiatCurrency("AUD"))
    currencies.append(FiatCurrency("RUB"))
    currencies.append(FiatCurrency("INR"))
    currencies.append(FiatCurrency("NGN"))
    
    currencies.sort(key=lambda x: x.name)
    
    default_fiat_currency = default_trade_currency if isinstance(default_trade_currency, FiatCurrency) else None
    if default_fiat_currency is not None and default_fiat_currency in currencies:
        currencies.remove(default_fiat_currency)
        currencies.insert(0, default_fiat_currency)

    return currencies

def get_main_crypto_currencies() -> list["CryptoCurrency"]:
    result = list["CryptoCurrency"]()
    result.append(CryptoCurrency("XRC", "XRhodium"))
    
    if DevEnv.is_dao_trading_activated():
        result.append(CryptoCurrency("BSQ", "BSQ"))
    
    result.append(CryptoCurrency("BEAM", "Beam"))
    result.append(CryptoCurrency("DASH", "Dash"))
    result.append(CryptoCurrency("DCR", "Decred"))
    result.append(CryptoCurrency("ETH", "Ether"))
    result.append(CryptoCurrency("GRIN", "Grin"))
    result.append(CryptoCurrency("L-BTC", "Liquid Bitcoin"))
    result.append(CryptoCurrency("LTC", "Litecoin"))
    result.append(CryptoCurrency("XMR", "Monero"))
    result.append(CryptoCurrency("NMC", "Namecoin"))
    result.append(CryptoCurrency("R-BTC", "RSK Smart Bitcoin"))
    result.append(CryptoCurrency("SF", "Siafund"))
    result.append(CryptoCurrency("ZEC", "Zcash"))
    result.sort(key=lambda x: x.name)
    
    return result

def get_removed_crypto_currencies() -> list["CryptoCurrency"]:
    result = list["CryptoCurrency"]()
    result.append(CryptoCurrency("BCH", "Bitcoin Cash"))
    result.append(CryptoCurrency("BCHC", "Bitcoin Clashic"))
    result.append(CryptoCurrency("ACH", "AchieveCoin"))
    result.append(CryptoCurrency("SC", "Siacoin"))
    result.append(CryptoCurrency("PPI", "PiedPiper Coin"))
    result.append(CryptoCurrency("PEPECASH", "Pepe Cash"))
    result.append(CryptoCurrency("GRC", "Gridcoin"))
    result.append(CryptoCurrency("LTZ", "LitecoinZ"))
    result.append(CryptoCurrency("ZOC", "01coin"))
    result.append(CryptoCurrency("BURST", "Burstcoin"))
    result.append(CryptoCurrency("STEEM", "Steem"))
    result.append(CryptoCurrency("DAC", "DACash"))
    result.append(CryptoCurrency("RDD", "ReddCoin"))
    return result

def get_all_fiat_currencies() -> list["FiatCurrency"]:
    return SORTED_BY_NAME_FIAT_CURRENCIES

def get_crypto_currency(currency_code: str) -> Optional["CryptoCurrency"]:
    return crypto_currency_map.get(currency_code, None)

def get_fiat_currency(currency_code: str) -> Optional["FiatCurrency"]:
    return CURRENCY_CODE_TO_FIAT_CURRENCY_MAP.get(currency_code, None)
