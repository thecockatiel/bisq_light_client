from typing import TYPE_CHECKING
from bisq.asset.tokens import TOKENS
from bisq.asset.coins import COINS

if TYPE_CHECKING:
    from bisq.asset.asset import Asset

class AssetRegistry:
    registered_assets: list["Asset"] = []


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

AssetRegistry.registered_assets.sort(key=lambda asset: asset.get_name())