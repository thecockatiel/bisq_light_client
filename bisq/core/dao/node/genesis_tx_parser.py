from typing import TYPE_CHECKING

from bisq.core.dao.node.parser.exceptions.invalid_genesis_tx_exception import (
    InvalidGenesisTxException,
)
from bisq.core.dao.node.parser.temp_tx import TempTx
from bisq.core.dao.state.model.blockchain.tx import Tx
from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
from bisq.core.dao.state.model.blockchain.tx_type import TxType

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.node.full.raw_tx import RawTx


class GenesisTxParser:
    @staticmethod
    def is_genesis(
        raw_tx: "RawTx", genesis_tx_id: str, genesis_block_height: int
    ) -> bool:
        return (
            raw_tx.block_height == genesis_block_height and raw_tx.id == genesis_tx_id
        )

    @staticmethod
    def get_genesis_tx(
        raw_tx: "RawTx", genesis_total_supply: int, dao_state_service: "DaoStateService"
    ) -> "Tx":
        genesis_tx = GenesisTxParser.get_genesis_temp_tx(raw_tx, genesis_total_supply)
        GenesisTxParser.commit_utxos(dao_state_service, genesis_tx)
        return Tx.from_temp_tx(genesis_tx)

    @staticmethod
    def commit_utxos(
        dao_state_service: "DaoStateService", genesis_tx: "TempTx"
    ) -> None:
        for temp_tx_output in genesis_tx.temp_tx_outputs:
            dao_state_service.add_unspent_tx_output(
                TxOutput.from_temp_output(temp_tx_output)
            )

    @staticmethod
    def get_genesis_temp_tx(raw_tx: "RawTx", genesis_total_supply: int) -> "TempTx":
        temp_tx = TempTx.from_raw_tx(raw_tx)
        temp_tx.tx_type = TxType.GENESIS
        remaining_input_value = genesis_total_supply
        temp_tx_outputs = temp_tx.temp_tx_outputs

        for tx_output in temp_tx_outputs:
            value = tx_output.value
            if value > remaining_input_value:
                raise InvalidGenesisTxException(
                    f"Genesis tx is invalid; using more than available inputs. "
                    f"Remaining input value is {remaining_input_value} sat; tx info: {temp_tx}"
                )

            remaining_input_value -= value
            tx_output.tx_output_type = TxOutputType.GENESIS_OUTPUT

        if remaining_input_value > 0:
            raise InvalidGenesisTxException(
                f"Genesis tx is invalid; not using all available inputs. "
                f"Remaining input value is {remaining_input_value} sat, tx info: {temp_tx}"
            )

        return temp_tx
