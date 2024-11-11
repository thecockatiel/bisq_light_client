import importlib
from types import SimpleNamespace
from bisq.asset.bisq_asset_asset import ASSET_TOKENS

TOKENS = SimpleNamespace()

for module_name in ASSET_TOKENS:
    module = importlib.import_module(f"bisq.asset.tokens.{module_name}")
    setattr(TOKENS, ASSET_TOKENS[module_name], module.__dict__[ASSET_TOKENS[module_name]])

