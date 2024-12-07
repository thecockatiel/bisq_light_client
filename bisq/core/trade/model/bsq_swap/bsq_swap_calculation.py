from bisq.common.util.math_utils import MathUtils
from bisq.core.monetary.volume import Volume
from bitcoinj.base.coin import Coin

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

# TODO: implemement as necessary

class BsqSwapCalculation:
    MIN_SELLERS_TX_SIZE = 104
    
    # Estimated size in case we do not have enough funds to calculate it from wallet inputs.
    # We use 3 non segwit inputs. 5 + 3*149 + 62 = 514
    ESTIMATED_V_BYTES = 514
    
    @staticmethod
    def get_bsq_trade_amount(volume: "Volume"):
        """Convert BTC trade amount to BSQ amount"""
        # We treat BSQ as altcoin with smallest unit exponent 8 but we use 2 instead.
        # To avoid a larger refactoring of the monetary domain we just hack in the conversion here
        # by removing the last 6 digits.
        
        return Coin.value_of(MathUtils.round_double_to_long(MathUtils.scale_down_by_power_of_10(volume.value, 6)))