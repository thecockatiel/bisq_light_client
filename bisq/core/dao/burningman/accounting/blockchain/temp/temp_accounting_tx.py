from decimal import Decimal
from typing import TYPE_CHECKING
from bisq.core.dao.burningman.accounting.blockchain.temp.temp_accounting_input import (
    TempAccountingTxInput,
)
from bisq.core.dao.burningman.accounting.blockchain.temp.temp_accounting_output import (
    TempAccountingTxOutput,
)

if TYPE_CHECKING:
    from bisq.core.dao.node.full.rpc.dto.raw_dto_transaction import RawDtoTransaction


class TempAccountingTx:

    def __init__(self, tx: "RawDtoTransaction"):
        self.tx_id = tx.tx_id

        # If lockTime is < 500000000 it is interpreted as block height, otherwise as unix time. We use block height.
        # We only handle blocks from EARLIEST_BLOCK_HEIGHT on
        # java TODO for dev testing: # tx.lock_time >= BurningManAccountingService.EARLIEST_BLOCK_HEIGHT and
        self.is_valid_dpt_lock_time = tx.lock_time < 500000000

        self.inputs = tuple(
            TempAccountingTxInput(input.sequence, input.tx_in_witness or tuple())
            for input in tx.vin
        )

        self.outputs = tuple(
            TempAccountingTxOutput(
                int(Decimal(output.value).scaleb(8).to_integral_exact()),
                (
                    output.script_pub_key.addresses[0]
                    if output.script_pub_key
                    and output.script_pub_key.addresses
                    and len(output.script_pub_key.addresses) == 1
                    else ""  #  We use a non-null value for address as in the final object we require that the address is available
                ),
                output.script_pub_key.type if output.script_pub_key else None,
            )
            for output in tx.vout
        )

    def __eq__(self, value):
        if not isinstance(value, TempAccountingTx):
            return False
        return (
            self.tx_id == value.tx_id
            and self.inputs == value.inputs
            and self.outputs == value.outputs
        )

    def __hash__(self):
        return hash((self.tx_id, self.inputs, self.outputs))
