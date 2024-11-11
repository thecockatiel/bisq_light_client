from bisq.asset.asset import Asset
from bisq.asset.coins.asset_registry import AssetRegistry
from bisq.core.locale.crypto_currency import CryptoCurrency
from bisq.core.locale.currency_data import (
    COUNTRY_TO_CURRENCY_CODE_MAP,
    CURRENCY_CODE_TO_DATA_MAP,
)
from bisq.core.locale.fiat_currency import FiatCurrency

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

def get_currency_by_country_code(country_code: str):
    currency_data = CURRENCY_CODE_TO_DATA_MAP.get(
        COUNTRY_TO_CURRENCY_CODE_MAP.get(country_code)
    )
    return FiatCurrency(currency_data)


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
