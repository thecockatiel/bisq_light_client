from typing import TYPE_CHECKING, Optional
from bisq.common.payload import Payload
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction


class TxInfo(Payload):

    # The client cannot see an instance of an org.bitcoinj.core.Transaction.  We use the
    # lighter weight TxInfo proto wrapper instead, containing just enough fields to
    # view some transaction details.  A block explorer or bitcoin-core client can be
    # used to see more detail.

    def __init__(
        self,
        tx_id: Optional[str] = None,
        input_sum: Optional[int] = None,
        output_sum: Optional[int] = None,
        fee: Optional[int] = None,
        size: Optional[int] = None,
        is_pending: Optional[bool] = None,
        memo: Optional[str] = None,
    ):
        self.tx_id = tx_id
        self.input_sum = input_sum
        self.output_sum = output_sum
        self.fee = fee
        self.size = size
        self.is_pending = is_pending
        self.memo = memo

    @staticmethod
    def from_transaction(transaction: "Transaction") -> "TxInfo":
        if transaction is None:
            raise IllegalStateException("server created a null transaction")

        tx_info = TxInfo(
            tx_id=transaction.get_tx_id(),
            input_sum=transaction.get_input_sum().value,
            output_sum=transaction.get_output_sum().value,
            size=transaction.get_message_size(),
            is_pending=transaction.is_pending,
            memo=transaction.memo,
        )
        tx_fee = transaction.get_fee()
        if tx_fee is not None:
            tx_info.fee = tx_fee.value
        return tx_info

    # //////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # //////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> grpc_pb2.TxInfo:
        return grpc_pb2.TxInfo(
            tx_id=self.tx_id,
            input_sum=self.input_sum,
            output_sum=self.output_sum,
            fee=self.fee,
            size=self.size,
            is_pending=self.is_pending,
            memo=self.memo or "",
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.TxInfo) -> "TxInfo":
        return TxInfo(
            tx_id=proto.tx_id,
            input_sum=proto.input_sum,
            output_sum=proto.output_sum,
            fee=proto.fee,
            size=proto.size,
            is_pending=proto.is_pending,
            memo=proto.memo,
        )

    def __str__(self) -> str:
        return (
            f"TxInfo{{\n"
            f"  tx_id='{self.tx_id}'\n"
            f"  input_sum={self.input_sum}\n"
            f"  output_sum={self.output_sum}\n"
            f"  fee={self.fee}\n"
            f"  size={self.size}\n"
            f"  is_pending={self.is_pending}\n"
            f"  memo='{self.memo}'\n"
            f"}}"
        )

    def get_transaction_detail_string(self, transaction: "Transaction") -> str:
        if transaction is None:
            raise IllegalStateException("Cannot print details for null transaction")

        builder = [
            f"Transaction {transaction.get_tx_id()}:",
            f"\tisPending:                    {transaction.is_pending}",
            f"\tfee:                          {transaction.get_fee()}",
            f"\tweight:                       {transaction.get_weight()}",
            f"\tVsize:                        {transaction.get_vsize()}",
            f"\tinputSum:                     {transaction.get_input_sum()}",
            f"\toutputSum:                    {transaction.get_output_sum()}",
        ]

        appears_in_hashes = transaction.appears_in_hashes
        if appears_in_hashes is not None:
            builder.append(f"\tappearsInHashes: yes, count:  {len(appears_in_hashes.keys())}")
        else:
            builder.append("\tappearsInHashes:              no")

        builder.extend([
            f"\tanyOutputSpent:               {transaction.is_any_output_spent()}",
            f"\tupdateTime:                   {transaction.get_update_time()}",
            f"\tincludedInBestChainAt:        {transaction.get_included_in_best_chain_at()}",
            f"\thasWitnesses:                 {transaction.has_witnesses}",
            f"\tlockTime:                     {transaction.lock_time}",
            f"\tversion:                      {transaction.version}",
            f"\tsigOpCount:                   {transaction.get_sig_op_count()}",
            f"\tisTimeLocked:                 {transaction.is_time_locked}",
            f"\thasRelativeLockTime:          {transaction.has_relative_lock_time}",
            f"\tisOptInFullRBF:               {transaction.is_opt_in_full_rbf}",
            f"\tmemo:                         {transaction.memo}",
            # purpose was omitted
        ])

        return "\n".join(builder)