from typing import TYPE_CHECKING, Union

from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.bisq_default_coin_selector import BisqDefaultCoinSelector
from bisq.core.btc.wallet.wallet_service import WalletService


if TYPE_CHECKING:
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction_output import TransactionOutput

logger = get_logger(__name__)


class BtcCoinSelector(BisqDefaultCoinSelector):
    """
    We use a specialized version of the CoinSelector based on the DefaultCoinSelector implementation.
    We lookup for spendable outputs which matches any of our addresses.
    """

    def __init__(
        self,
        addresses: Union[set["Address"], "Address"],
        ignore_dust_threshold: int,
        permit_foreign_pending_tx=True,
    ):
        super().__init__(permit_foreign_pending_tx)
        assert addresses is not None, "addresses must not be None"
        self._addresses = addresses if isinstance(addresses, set) else {addresses}
        self._ignore_dust_threshold = ignore_dust_threshold

    def is_tx_output_spendable(self, output: "TransactionOutput") -> bool:
        if WalletService.is_output_script_convertible_to_address(output):
            address = WalletService.get_address_from_output(output)
            return address in self._addresses
        else:
            logger.warning(
                "transactionOutput.getScriptPubKey() is not P2PKH nor P2SH nor P2WH"
            )
            return False

    # We ignore utxos which are considered dust attacks for spying on users' wallets.
    # The ignoreDustThreshold value is set in the preferences. If not set we use default non dust
    # value of 546 sat. (600 ?)
    def is_dust_attack_utxo(self, output: "TransactionOutput") -> bool:
        return output.value < self._ignore_dust_threshold
