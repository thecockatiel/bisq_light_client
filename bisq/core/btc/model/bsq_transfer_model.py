from typing import TYPE_CHECKING
from bisq.core.dao.state.model.blockchain.tx_type import TxType


if TYPE_CHECKING:
    from bitcoinj.base.coin import Coin
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction import Transaction


class BsqTransferModel:
    def __init__(
        self,
        receiver_address: "Address",
        receiver_amount: "Coin",
        prepared_send_tx: "Transaction",
        tx_with_btc_fee: "Transaction",
        signed_tx: "Transaction",
    ):
        self.receiver_address = receiver_address
        self.receiver_amount = receiver_amount
        self.prepared_send_tx = prepared_send_tx
        self.tx_with_btc_fee = tx_with_btc_fee
        self.signed_tx = signed_tx
        self.mining_fee = signed_tx.get_fee()
        self.tx_size = len(signed_tx.bitcoin_serialize())
        self.tx_type = TxType.TRANSFER_BSQ

    def get_receiver_address_as_string(self) -> str:
        return str(self.receiver_address)

    def get_tx_size_in_kb(self) -> float:
        return self.tx_size / 1000.0

    def to_short_string(self) -> str:
        return (
            "{\n"
            f"  receiverAddress='{self.get_receiver_address_as_string()}'\n"
            f", receiverAmount={self.receiver_amount}\n"
            f", txWithBtcFee.txId={self.tx_with_btc_fee.get_tx_id()}\n"
            f", miningFee={self.mining_fee}\n"
            f", txSizeInKb={self.get_tx_size_in_kb()}\n"
            "}"
        )

    def __str__(self) -> str:
        return (
            "BsqTransferModel{\n"
            f"  receiverAddress='{self.get_receiver_address_as_string()}'\n"
            f", receiverAmount={self.receiver_amount}\n"
            f", preparedSendTx={self.prepared_send_tx}\n"
            f", txWithBtcFee={self.tx_with_btc_fee}\n"
            f", signedTx={self.signed_tx}\n"
            f", miningFee={self.mining_fee}\n"
            f", txSize={self.tx_size}\n"
            f", txSizeInKb={self.get_tx_size_in_kb()}\n"
            f", txType={self.tx_type}\n"
            "}"
        )
