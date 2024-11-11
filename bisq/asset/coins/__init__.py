import importlib
from types import SimpleNamespace
from bisq.asset.bisq_asset_asset import ASSET_COINS

COINS = SimpleNamespace()

for module_name in ASSET_COINS:
    module = importlib.import_module(f"bisq.asset.coins.{module_name}")
    setattr(COINS, ASSET_COINS[module_name], module.__dict__[ASSET_COINS[module_name]])

