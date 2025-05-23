# taken from https://github.com/bisq-network/bisq/blob/v1.9.17/assets/src/main/resources/META-INF/services/bisq.asset.Asset
# keep this updated with the latest version from the bisq repository and also make sure the coins and tokens exist.
import re

from utils.formatting import to_snake_case


_bisq_assets = """
# All assets available for trading on the Bisq network.
# Contents are sorted according to the output of `sort --ignore-case --dictionary-order`.
# See bisq.asset.Asset and bisq.asset.AssetRegistry for further details.
# See https://bisq.network/list-asset for complete instructions.
bisq.asset.coins.Actinium
bisq.asset.coins.Adeptio
bisq.asset.coins.Aeon
bisq.asset.coins.Amitycoin
bisq.asset.coins.Animecoin
bisq.asset.coins.Arqma
bisq.asset.coins.Askcoin
bisq.asset.coins.Australiacash
bisq.asset.coins.Beam
bisq.asset.coins.Bitcoin$Mainnet
bisq.asset.coins.Bitcoin$Regtest
bisq.asset.coins.BitcoinRhodium
bisq.asset.coins.Bitcoin$Testnet
bisq.asset.coins.BitDaric
bisq.asset.coins.Bitmark
bisq.asset.coins.Bitzec
bisq.asset.coins.Blur
bisq.asset.coins.BSQ$Mainnet
bisq.asset.coins.BSQ$Regtest
bisq.asset.coins.BSQ$Testnet
bisq.asset.coins.BurntBlackCoin
bisq.asset.coins.Cash2
bisq.asset.coins.Chaucha
bisq.asset.coins.CloakCoin
bisq.asset.coins.Counterparty
bisq.asset.coins.Credits
bisq.asset.coins.Croat
bisq.asset.coins.CRowdCLassic
bisq.asset.coins.CTSCoin
bisq.asset.coins.DarkPay
bisq.asset.coins.Dash
bisq.asset.coins.Decred
bisq.asset.coins.DeepOnion
bisq.asset.coins.Dextro
bisq.asset.coins.Dogecoin
bisq.asset.coins.Doichain
bisq.asset.coins.Donu
bisq.asset.coins.Dragonglass
bisq.asset.coins.DSTRA
bisq.asset.coins.Emercoin
bisq.asset.coins.Ergo
bisq.asset.coins.Ether
bisq.asset.coins.EtherClassic
bisq.asset.coins.Faircoin
bisq.asset.coins.FourtyTwo
bisq.asset.coins.Fujicoin
bisq.asset.coins.Galilel
bisq.asset.coins.GambleCoin
bisq.asset.coins.Genesis
bisq.asset.coins.Grin
bisq.asset.coins.Hatch
bisq.asset.coins.Helium
bisq.asset.coins.Horizen
bisq.asset.coins.IdaPay
bisq.asset.coins.Iridium
bisq.asset.coins.Kekcoin
bisq.asset.coins.KnowYourDeveloper
bisq.asset.coins.Kore
bisq.asset.coins.Krypton
bisq.asset.coins.LBRYCredits
bisq.asset.coins.LiquidBitcoin
bisq.asset.coins.Litecoin
bisq.asset.coins.LitecoinPlus
bisq.asset.coins.LitecoinZ
bisq.asset.coins.Lytix
bisq.asset.coins.Masari
bisq.asset.coins.Mask
bisq.asset.coins.Mile
bisq.asset.coins.MirQuiX
bisq.asset.coins.MobitGlobal
bisq.asset.coins.Monero
bisq.asset.coins.MonetaryUnit
bisq.asset.coins.MoX
bisq.asset.coins.Myce
bisq.asset.coins.Namecoin
bisq.asset.coins.Navcoin
bisq.asset.coins.Ndau
bisq.asset.coins.Noir
bisq.asset.coins.NoteBlockchain
bisq.asset.coins.ParsiCoin
bisq.asset.coins.Particl
bisq.asset.coins.PENG
bisq.asset.coins.Persona
bisq.asset.coins.Pinkcoin
bisq.asset.coins.PIVX
bisq.asset.coins.Plenteum
bisq.asset.coins.PZDC
bisq.asset.coins.Qbase
bisq.asset.coins.QMCoin
bisq.asset.coins.Qwertycoin
bisq.asset.coins.Radium
bisq.asset.coins.Remix
bisq.asset.coins.RSKSmartBitcoin
bisq.asset.coins.Ryo
bisq.asset.coins.Siafund
bisq.asset.coins.SiaPrimeCoin
bisq.asset.coins.SixEleven
bisq.asset.coins.Solo
bisq.asset.coins.SpaceCash
bisq.asset.coins.Spectrecoin
bisq.asset.coins.Starwels
bisq.asset.coins.SUB1X
bisq.asset.coins.TEO
bisq.asset.coins.TurtleCoin
bisq.asset.coins.UnitedCommunityCoin
bisq.asset.coins.Unobtanium
bisq.asset.coins.uPlexa
bisq.asset.coins.VARIUS
bisq.asset.coins.Veil
bisq.asset.coins.Vertcoin
bisq.asset.coins.Webchain
bisq.asset.coins.WORX
bisq.asset.coins.WrkzCoin
bisq.asset.coins.XDR
bisq.asset.coins.Zcash
bisq.asset.coins.Zcoin
bisq.asset.coins.ZelCash
bisq.asset.coins.Zero
bisq.asset.coins.ZeroClassic
bisq.asset.tokens.AugmintEuro
bisq.asset.tokens.DaiStablecoin
bisq.asset.tokens.EtherStone
bisq.asset.tokens.TetherUSDERC20
bisq.asset.tokens.TrueUSD
bisq.asset.tokens.USDCoin
bisq.asset.tokens.VectorspaceAI
"""

# get words after tokens. and coins. in separate lists and dedupe for $ cases while preserving the order
ASSET_TOKENS = re.findall(r"tokens\.(\w+)", _bisq_assets)
ASSET_COINS = re.findall(r"coins\.(\w+)", _bisq_assets)
ASSET_TOKENS: dict[str, str] = dict.fromkeys(ASSET_TOKENS)
ASSET_COINS: dict[str, str] = dict.fromkeys(ASSET_COINS)

# snake case the names
# snake_case(x) for x in ASSET_TOKENS
ASSET_TOKENS = {to_snake_case(x): x for x in ASSET_TOKENS}
ASSET_COINS = {to_snake_case(x): x for x in ASSET_COINS}
