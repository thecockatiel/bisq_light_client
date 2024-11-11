from bisq.asset.tokens import TOKENS
from bisq.asset.coins import COINS


class AssetRegistry:
    registered_assets = []


for asset in list(TOKENS.__dict__.values()):
    AssetRegistry.registered_assets.append(asset())

# NOTE: we currently only support mainnet networks.
for asset in COINS.__dict__:
    if asset == "Bitcoin":
        AssetRegistry.registered_assets.append(COINS.__dict__[asset].Mainnet())
    elif asset == "BSQ":
        AssetRegistry.registered_assets.append(COINS.__dict__[asset].Mainnet())
    else:
        AssetRegistry.registered_assets.append(COINS.__dict__[asset]())
