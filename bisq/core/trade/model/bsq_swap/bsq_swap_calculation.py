from typing import TYPE_CHECKING, Optional, Union
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.monetary.volume import Volume
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade

"""
The fees can be paid either by adding them to the inputs or by reducing them from the outputs. As we want to avoid
extra inputs only needed for the fees (tx fee in case of buyer and trade fee in case of seller) we let
the buyer add the trade fee to the BSQ input and reduce the tx fee from the BTC output. For the seller its the
other way round.


The example numbers are:
BTC trade amount 100000000 sat (1 BTC)
BSQ trade amount: 5000000 sat (50000.00 BSQ)
Buyer trade fee: 50 sat (0.5 BSQ)
Seller trade fee: 150 sat (1.5 BSQ)
Buyer tx fee:  1950 sat (total tx fee would be 2000 but we subtract the 50 sat trade fee)
Seller tx fee:  1850 sat (total tx fee would be 2000 but we subtract the 150 sat trade fee)

Input buyer: BSQ trade amount + buyer trade fee                                              5000000 + 50
Input seller: BTC trade amount + seller tx fee                                               100000000 + 1850
Output seller: BSQ trade amount - sellers trade fee                                          5000000 - 150
Output buyer:  BSQ change                                                                    0
Output buyer:  BTC trade amount - buyers tx fee                                              100000000 - 1950
Output seller:  BTC change                                                                   0
Tx fee: Buyer tx fee + seller tx fee + buyer trade fee + seller trade fee                    1950 + 1850 + 50 + 150
"""

logger = get_logger(__name__)


# TODO: implemement as necessary
class BsqSwapCalculation:
    MIN_SELLERS_TX_SIZE = 104

    # Estimated size in case we do not have enough funds to calculate it from wallet inputs.
    # We use 3 non segwit inputs. 5 + 3*149 + 62 = 514
    ESTIMATED_VBYTES = 514

    @staticmethod
    def get_buyers_bsq_input_value(
        bsq_trade_amount: Union[int, "BsqSwapTrade"],
        buyers_trade_fee: int,
    ) -> Coin:
        if hasattr(bsq_trade_amount, "get_bsq_trade_amount"):
            bsq_trade_amount = bsq_trade_amount.get_bsq_trade_amount()
        return Coin.value_of(bsq_trade_amount + buyers_trade_fee)

    @staticmethod
    def get_sellers_btc_input_value(
        btc_trade_amount: int,
        seller_tx_fee: int,
    ) -> Coin:
        return Coin.value_of(btc_trade_amount + seller_tx_fee)

    @staticmethod
    def get_sellers_btc_input_value_with_adjustment(
        btc_trade_amount: int,
        tx_fee_per_vbyte: int,
        sellers_vbytes_size: int,
        sellers_trade_fee: int,
    ) -> Coin:
        sellers_tx_fee = BsqSwapCalculation.get_adjusted_tx_fee(
            tx_fee_per_vbyte, sellers_vbytes_size, sellers_trade_fee
        )
        return BsqSwapCalculation.get_sellers_btc_input_value(
            btc_trade_amount, sellers_tx_fee
        )

    @staticmethod
    def get_sellers_btc_input_value_from_wallet(
        btc_wallet_service: "BtcWalletService",
        btc_trade_amount: "Coin",
        tx_fee_per_vbyte: int,
        sellers_trade_fee: int,
    ) -> Coin:
        inputs_and_change = BsqSwapCalculation.get_sellers_btc_inputs_and_change(
            btc_wallet_service,
            btc_trade_amount.value,
            tx_fee_per_vbyte,
            sellers_trade_fee,
        )
        sellers_vbytes_size = BsqSwapCalculation.get_vbytes_size(
            inputs_and_change[0], inputs_and_change[1].value
        )
        sellers_tx_fee = BsqSwapCalculation.get_adjusted_tx_fee(
            tx_fee_per_vbyte, sellers_vbytes_size, sellers_trade_fee
        )
        return BsqSwapCalculation.get_sellers_btc_input_value(
            btc_trade_amount.value, sellers_tx_fee
        )

    # Tx fee estimation
    @staticmethod
    def get_sellers_btc_inputs_and_change(
        btc_wallet_service: "BtcWalletService",
        amount: int,
        tx_fee_per_vbyte: int,
        sellers_trade_fee: int,
    ) -> tuple[list["RawTransactionInput"], Coin]:
        # Figure out how large out tx will be
        iterations = 0
        previous: Optional[Coin] = None
        inputs_and_change: tuple[list["RawTransactionInput"], Coin] = None

        # At first we try with min. tx size
        sellers_tx_size = BsqSwapCalculation.MIN_SELLERS_TX_SIZE
        change = Coin.ZERO()
        required = BsqSwapCalculation.get_sellers_btc_input_value_with_adjustment(
            amount,
            tx_fee_per_vbyte,
            sellers_tx_size,
            sellers_trade_fee,
        )

        # We do a first calculation here to get the size of the inputs (segwit or not) and we adjust the sellersTxSize
        # so that we avoid to get into dangling states.
        inputs_and_change = btc_wallet_service.get_inputs_and_change(required)
        sellers_tx_size = BsqSwapCalculation.get_vbytes_size(inputs_and_change[0], 0)
        required = BsqSwapCalculation.get_sellers_btc_input_value_with_adjustment(
            amount,
            tx_fee_per_vbyte,
            sellers_tx_size,
            sellers_trade_fee,
        )

        # As fee calculation is not deterministic it could be that we toggle between a too small and too large
        # inputs. We would take the latest result before we break iteration. Worst case is that we under- or
        # overpay a bit. As fee rate is anyway an estimation we ignore that imperfection.
        while iterations < 10 and required != previous:
            inputs_and_change = btc_wallet_service.get_inputs_and_change(required)
            previous = required

            # We calculate more exact tx size based on resulted inputs and change
            change = inputs_and_change[1]
            if Restrictions.is_dust(change):
                logger.warning(
                    "We got a change below dust. We ignore that and use it as miner fee."
                )
                change = Coin.ZERO()

            sellers_tx_size = BsqSwapCalculation.get_vbytes_size(
                inputs_and_change[0],
                change.value,
            )
            required = BsqSwapCalculation.get_sellers_btc_input_value_with_adjustment(
                amount,
                tx_fee_per_vbyte,
                sellers_tx_size,
                sellers_trade_fee,
            )

            iterations += 1

        assert inputs_and_change is not None

        return inputs_and_change

    @staticmethod
    def get_vbytes_size(inputs: list["RawTransactionInput"], change: int):
        # See https://bitcoin.stackexchange.com/questions/87275/how-to-calculate-segwit-transaction-fee-in-bytes
        size = 5  # Half of base tx size (10)
        for input in inputs:
            size += 68 if input.is_segwit else 149
        size += 62 if change > 0 else 31
        return size

    @staticmethod
    def get_adjusted_tx_fee(
        tx_fee_per_vbyte: Union[int, "BsqSwapTrade"], vbytes: int, trade_fee: int
    ) -> int:
        if hasattr(tx_fee_per_vbyte, "tx_fee_per_vbyte"):
            tx_fee_per_vbyte = tx_fee_per_vbyte.tx_fee_per_vbyte

        return tx_fee_per_vbyte * vbytes - trade_fee

    @staticmethod
    def get_bsq_trade_amount(volume: "Volume"):
        """Convert BTC trade amount to BSQ amount"""
        # We treat BSQ as altcoin with smallest unit exponent 8 but we use 2 instead.
        # To avoid a larger refactoring of the monetary domain we just hack in the conversion here
        # by removing the last 6 digits.

        return Coin.value_of(
            MathUtils.round_double_to_long(
                MathUtils.scale_down_by_power_of_10(volume.value, 6)
            )
        )
