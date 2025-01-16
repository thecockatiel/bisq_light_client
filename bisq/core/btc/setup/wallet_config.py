from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bitcoinj.wallet.wallet import Wallet


logger = get_logger(__name__)


# TODO
class WalletConfig:

    def maybe_add_segwit_keychain(
        self, wallet: "Wallet", aes_key: bytes, is_bsq_wallet: bool
    ):
        raise RuntimeError("WalletConfig.maybe_add_segwit_keychain Not implemented yet")

    def btc_wallet(self) -> "Wallet":
        raise RuntimeError("WalletConfig.btc_wallet Not implemented yet")

    def bsq_wallet(self) -> "Wallet":
        raise RuntimeError("WalletConfig.bsq_wallet Not implemented yet")
