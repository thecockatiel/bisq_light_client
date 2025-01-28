from abc import ABC, abstractmethod
from functools import total_ordering
from typing import TYPE_CHECKING, Iterable, Optional

from bisq.core.btc.wallet.restrictions import Restrictions
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction_confidence_source import TransactionConfidenceSource
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.wallet.coin_selector import CoinSelector


if TYPE_CHECKING:
    from bitcoinj.base.coin import Coin
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.wallet.coin_selection import CoinSelection


class BisqDefaultCoinSelector(CoinSelector, ABC):

    def __init__(self, permit_foreign_pending_tx: bool):
        self.permit_foreign_pending_tx = permit_foreign_pending_tx
        # TransactionOutputs to be used as candidates in the select method.
        # We reset the value to None just after we have applied it inside the select method.
        self.utxo_candidates: Optional[set["TransactionOutput"]] = None
        
    def select(self, target: "Coin", candidates: Iterable["TransactionOutput"]) -> "CoinSelection":
        selected: list["TransactionOutput"] = []
        # Sort the inputs by age*value so we get the highest "coin days" spent.

        if self.utxo_candidates is not None:
            sorted_outputs = list(self.utxo_candidates)
        else:
            sorted_outputs = list(candidates)

        # If we spend all we don't need to sort
        if target != NetworkParameters.MAX_MONEY:
            BisqDefaultCoinSelector.sort_outputs(sorted_outputs)

        # Now iterate over the sorted outputs until we have got as close to the target as possible or a little
        # bit over (excessive value will be change).
        total = 0
        target_value = target.value
        for output in sorted_outputs:
            if not self.is_dust_attack_utxo(output):
                if total >= target_value:
                    change = total - target_value
                    if change == 0 or change >= Restrictions.get_min_non_dust_output().value:
                        break

            if (output.parent is not None and
                self.is_tx_spendable(output.parent) and
                self.is_tx_output_spendable(output)):
                selected.append(output)
                total += output.value

        # Total may be lower than target here, if the given candidates were insufficient to create the requested
        # transaction.
        return CoinSelection(Coin.value_of(total), selected)
    
    @abstractmethod
    def is_dust_attack_utxo(self, output: "TransactionOutput") -> bool:
        pass
    
    def get_change(self, target: "Coin", coin_selection: "CoinSelection") -> "Coin":
        value = target.value
        available = coin_selection.value_gathered.value
        change = available - value
        if change < 0:
            raise ValueError(f"Insufficient money: missing {Coin.value_of(change * -1)}")
        return Coin.value_of(change)

    # We allow spending from own unconfirmed txs and if permitForeignPendingTx is set as well from foreign
    # unconfirmed txs.  
    def is_tx_spendable(self, tx: "Transaction") -> bool:
        confidence = tx.get_confidence()
        type = confidence.confidence_type
        is_confirmed = type == TransactionConfidenceType.BUILDING
        is_pending = type == TransactionConfidenceType.PENDING
        is_own_tx = confidence.confidence_source == TransactionConfidenceSource.SELF
        return is_confirmed or (is_pending and (self.permit_foreign_pending_tx or is_own_tx))
    
    @abstractmethod
    def is_tx_output_spendable(self, output: "TransactionOutput") -> bool:
        pass
    
    # JAVA TODO Why it uses coin age and not try to minimize number of inputs as the highest priority?
    #      Asked Oscar and he also don't knows why coin age is used. Should be changed so that min. number of inputs is
    #      target.
    def sort_outputs(outputs: list["TransactionOutput"]) -> None:
        outputs.sort(key=_TransactionOutputCompare)
       
@total_ordering 
class _TransactionOutputCompare:
    def __init__(self, output: "TransactionOutput"):
        self.output = output
        
    def __eq__(self, other: "_TransactionOutputCompare") -> bool:
        if not isinstance(other, _TransactionOutputCompare):
            return NotImplemented
        return (self.output.value == other.output.value and 
                self.output.get_parent_transaction_depth_in_blocks() == other.output.get_parent_transaction_depth_in_blocks() and
                self.output.get_parent_transaction_hash() == other.output.get_parent_transaction_hash())
    
    def __lt__(self, other: "_TransactionOutputCompare") -> bool:
        if not isinstance(other, _TransactionOutputCompare):
            return NotImplemented
            
        # Compare by coin depth (value * block depth)
        depth1 = self.output.get_parent_transaction_depth_in_blocks()
        depth2 = other.output.get_parent_transaction_depth_in_blocks()
        value1 = self.output.value
        value2 = other.output.value
        coin_depth1 = value1 * depth1
        coin_depth2 = value2 * depth2
        
        if coin_depth1 != coin_depth2:
            return coin_depth1 > coin_depth2
            
        # If coin depths are equal, compare by value
        if value1 != value2:
            return value1 > value2
            
        # If values are equal, compare by hash
        hash1 = int.from_bytes(bytes.fromhex(self.output.get_parent_transaction_hash()), byteorder='big', signed=False) if self.output.get_parent_transaction_hash() else 0
        hash2 = int.from_bytes(bytes.fromhex(other.output.get_parent_transaction_hash()), byteorder='big', signed=False) if other.output.get_parent_transaction_hash() else 0
        
        return hash1 < hash2  # Note: reversed comparison from Java to match the sorting requirements

