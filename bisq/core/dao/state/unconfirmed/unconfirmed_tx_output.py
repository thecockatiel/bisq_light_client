from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bitcoinj.core.transaction_output import TransactionOutput

logger = get_logger(__name__)


class UnconfirmedTxOutput(PersistablePayload, ImmutableDaoStateModel):
    """
    Used for tracking unconfirmed change outputs to allow them to be spent in follow up
    transactions in txType permits it. We can assume that the user is not intending to
    double spend own transactions as well that he does not try to spend an invalid BSQ
    output to a BSQ address.
    We do not allow spending unconfirmed BSQ outputs received from elsewhere.
    """

    def __init__(self, index: int, value: int, tx_id: str):
        self.index = index
        self.value = value
        self.tx_id = tx_id

    def to_proto_message(self) -> protobuf.UnconfirmedTxOutput:
        return protobuf.UnconfirmedTxOutput(
            index=self.index, value=self.value, tx_id=self.tx_id
        )

    @staticmethod
    def from_proto(proto: protobuf.UnconfirmedTxOutput) -> "UnconfirmedTxOutput":
        return UnconfirmedTxOutput(
            index=proto.index, value=proto.value, tx_id=proto.tx_id
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def key(self) -> "TxOutputKey":
        return TxOutputKey(self.tx_id, self.index)

    def __str__(self) -> str:
        return (
            "UnconfirmedTxOutput{\n"
            f"     index={self.index},\n"
            f"     value={self.value},\n"
            f"     txId='{self.tx_id}'\n"
            "}"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def from_transaction_output(
        transaction_output: "TransactionOutput",
    ) -> "UnconfirmedTxOutput":
        parent_transaction = transaction_output.parent
        if parent_transaction is not None:
            return UnconfirmedTxOutput(
                index=transaction_output.index,
                value=transaction_output.get_value().value,
                tx_id=parent_transaction.get_tx_id(),
            )
        else:
            logger.warning(
                "parentTransaction of transactionOutput is None. "
                "This must not happen. "
                "We could throw an exception as well "
                "here but we prefer to be for now more tolerant and just "
                f"assign the value 0 if that would be the case. transactionOutput={transaction_output}",
            )
            return UnconfirmedTxOutput(
                index=transaction_output.index, value=0, tx_id="null"
            )
