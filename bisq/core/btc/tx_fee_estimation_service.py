from typing import TYPE_CHECKING, List, Tuple
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.preconditions import check_argument
from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException


if TYPE_CHECKING:
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    
    
logger = get_logger(__name__)


class TxFeeEstimationService:
    """Util class for getting the estimated tx fee for maker or taker fee tx."""

    # Size/vsize of typical trade txs
    # Real txs size/vsize may vary in 1 or 2 bytes from the estimated values.
    # Values calculated with https://gist.github.com/oscarguindzberg/3d1349cb65d9fd9af9de0feaa3fd27ac
    # legacy fee tx with 1 input, maker/taker fee paid in btc size/vsize = 258
    # legacy deposit tx without change size/vsize = 381
    # legacy deposit tx with change size/vsize = 414
    # legacy payout tx size/vsize = 337
    # legacy delayed payout tx size/vsize = 302
    # segwit fee tx with 1 input, maker/taker fee paid in btc vsize = 173
    # segwit deposit tx without change vsize = 232
    # segwit deposit tx with change vsize = 263
    # segwit payout tx vsize = 169
    # segwit delayed payout tx vsize = 139
    TYPICAL_TX_WITH_1_INPUT_VSIZE = 175
    DEPOSIT_TX_VSIZE = 233

    BSQ_INPUT_INCREASE = 70
    MAX_ITERATIONS = 10

    def __init__(
        self,
        fee_service: "FeeService",
        btc_wallet_service: "BtcWalletService",
        preferences: "Preferences",
    ):
        self.fee_service = fee_service
        self.btc_wallet_service = btc_wallet_service
        self.preferences = preferences

    def get_estimated_fee_and_tx_vsize_for_taker(
        self, funds_needed_for_trade: Coin, trade_fee: Coin
    ) -> Tuple[Coin, int]:
        return self.get_estimated_fee_and_tx_vsize(
            True,
            funds_needed_for_trade,
            trade_fee,
            self.fee_service,
            self.btc_wallet_service,
            self.preferences,
        )

    def get_estimated_fee_and_tx_vsize_for_maker(
        self, reserved_funds_for_offer: Coin, trade_fee: Coin
    ) -> Tuple[Coin, int]:
        return self.get_estimated_fee_and_tx_vsize(
            False,
            reserved_funds_for_offer,
            trade_fee,
            self.fee_service,
            self.btc_wallet_service,
            self.preferences,
        )

    def get_estimated_fee_and_tx_vsize(
        self,
        is_taker: bool,
        amount: Coin,
        trade_fee: Coin,
        fee_service: "FeeService",
        btc_wallet_service: "BtcWalletService",
        preferences: "Preferences",
    ) -> Tuple[Coin, int]:
        tx_fee_per_vbyte = fee_service.get_tx_fee_per_vbyte()
        # We start with min taker fee vsize of 175
        estimated_tx_vsize = TxFeeEstimationService.TYPICAL_TX_WITH_1_INPUT_VSIZE
        try:
            estimated_tx_vsize = self.get_estimated_tx_vsize(
                [trade_fee, amount],
                estimated_tx_vsize,
                tx_fee_per_vbyte,
                btc_wallet_service,
            )
        except InsufficientMoneyException:
            if is_taker:
                # If we cannot do the estimation, we use the vsize o the largest of our txs which is the deposit tx.
                estimated_tx_vsize = TxFeeEstimationService.DEPOSIT_TX_VSIZE
            logger.info(
                "We cannot do the fee estimation because there are not enough funds in the wallet. This is expected "
                f"if the user pays from an external wallet. In that case we use an estimated tx vsize of {estimated_tx_vsize} vbytes.",
            )

        if not preferences.is_pay_fee_in_btc():
            # If we pay the fee in BSQ we have one input more which adds about 150 bytes
            # JAVA TODO: Clarify if there is always just one additional input or if there can be more.
            estimated_tx_vsize += TxFeeEstimationService.BSQ_INPUT_INCREASE

        if is_taker:
            average_vsize = (estimated_tx_vsize + TxFeeEstimationService.DEPOSIT_TX_VSIZE) // 2 # deposit tx has about 233 vbytes
            # We use at least the vsize of the deposit tx to not underpay it.
            vsize = max(TxFeeEstimationService.DEPOSIT_TX_VSIZE, average_vsize)
            tx_fee = tx_fee_per_vbyte.multiply(vsize)
            logger.info(
                f"Fee estimation resulted in a tx vsize of {estimated_tx_vsize} vbytes.\n"
                f"We use an average between the taker fee tx and the deposit tx (233 vbytes) which results in {average_vsize} vbytes.\n"
                f"The deposit tx has 233 vbytes, we use that as our min value. Vsize for fee calculation is {vsize} vbytes.\n"
                f"The tx fee of {tx_fee.value} Sat"
            )
        else:
            vsize = estimated_tx_vsize
            tx_fee = tx_fee_per_vbyte.multiply(vsize)
            logger.info(
                f"Fee estimation resulted in a tx vsize of {vsize} vbytes and a tx fee of {tx_fee.value} Sat."
            )

        return tx_fee, vsize

    def get_estimated_fee_and_tx_vsize_simple(
        self, amount: Coin, btc_wallet_service: "BtcWalletService"
    ) -> Tuple[Coin, int]:
        tx_fee_per_vbyte = btc_wallet_service.get_tx_fee_for_withdrawal_per_vbyte()
        # We start with min taker fee vsize of 175
        estimated_tx_vsize = TxFeeEstimationService.TYPICAL_TX_WITH_1_INPUT_VSIZE
        try:
            estimated_tx_vsize = self.get_estimated_tx_vsize(
                [amount], estimated_tx_vsize, tx_fee_per_vbyte, btc_wallet_service
            )
        except InsufficientMoneyException:
            logger.info(
                "We cannot do the fee estimation because there are not enough funds in the wallet. This is expected "
                f"if the user pays from an external wallet. In that case we use an estimated tx vsize of {estimated_tx_vsize} vbytes."
            )

        tx_fee = tx_fee_per_vbyte.multiply(estimated_tx_vsize)
        logger.info(
            f"Fee estimation resulted in a tx vsize of {estimated_tx_vsize} vbytes and a tx fee of {tx_fee.value} Sat.",
        )

        return tx_fee, estimated_tx_vsize


    # We start with the initialEstimatedTxVsize for a tx with 1 input (175) vbytes and get from BitcoinJ a tx back which
    # contains the required inputs to fund that tx (outputs + miner fee). The miner fee in that case is based on
    # the assumption that we only need 1 input. Once we receive back the real tx vsize from the tx BitcoinJ has created
    # with the required inputs we compare if the vsize is not more then 20% different to our assumed tx vsize. If we are inside
    # that tolerance we use that tx vsize for our fee estimation, if not (if there has been more then 1 inputs) we
    # apply the new fee based on the reported tx vsize and request again from BitcoinJ to fill that tx with the inputs
    # to be sufficiently funded. The algorithm how BitcoinJ selects utxos is complex and contains several aspects
    # (minimize fee, don't create too many tiny utxos,...). We treat that algorithm as an unknown and it is not
    # guaranteed that there are more inputs required if we increase the fee (it could be that there is a better
    # selection of inputs chosen if we have increased the fee and therefore less inputs and smaller tx vsize). As the increased fee might
    # change the number of inputs we need to repeat that process until we are inside of a certain tolerance. To avoid
    # potential endless loops we add a counter (we use 10, usually it takes just very few iterations).
    # Worst case would be that the last vsize we got reported is > 20% off to
    # the real tx vsize but as fee estimation is anyway a educated guess in the best case we don't worry too much.
    # If we have underpaid the tx might take longer to get confirmed.
    @staticmethod
    def get_estimated_tx_vsize(
        output_values: List[Coin],
        initial_estimated_tx_vsize: int,
        tx_fee_per_vbyte: Coin,
        btc_wallet_service: "BtcWalletService",
    ) -> int:
        is_in_tolerance = False
        estimated_tx_vsize = initial_estimated_tx_vsize
        real_tx_vsize = 0
        counter = 0
        while not is_in_tolerance and counter < TxFeeEstimationService.MAX_ITERATIONS:
            tx_fee = tx_fee_per_vbyte.multiply(estimated_tx_vsize)
            real_tx_vsize = btc_wallet_service.get_estimated_fee_tx_vsize(
                output_values, tx_fee
            )
            is_in_tolerance = TxFeeEstimationService.is_in_tolerance(
                estimated_tx_vsize, real_tx_vsize, 0.2
            )
            if not is_in_tolerance:
                estimated_tx_vsize = real_tx_vsize
            counter += 1

        if not is_in_tolerance:
            logger.warning(
                f"We could not find a tx which satisfies our tolerance requirement of 20%. realTxVsize={real_tx_vsize}, estimatedTxVsize={estimated_tx_vsize}"
            )
        return estimated_tx_vsize

    @staticmethod
    def is_in_tolerance(estimated_vsize: int, tx_vsize: int, tolerance: float) -> bool:
        check_argument(estimated_vsize > 0, "estimated_vsize must be positive")
        check_argument(tx_vsize > 0, "tx_vsize must be positive")
        check_argument(tolerance > 0, "tolerance must be positive")
        deviation = abs(1 - (estimated_vsize / tx_vsize))
        return deviation <= tolerance
