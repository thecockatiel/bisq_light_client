from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.encryption import Encryption
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.proofofburn.my_proof_of_burn import MyProofOfBurn
from bisq.core.dao.governance.proofofburn.proof_of_burn_consensus import (
    ProofOfBurnConsensus,
)
from bisq.core.dao.governance.proposal.tx_exception import TxException
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from utils.data import SimpleProperty

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.governance.proofofburn.my_proof_of_burn_service import (
        MyProofOfBurnListService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.blockchain.tx import Tx

logger = get_logger(__name__)


class ProofOfBurnService(DaoSetupService, DaoStateListener):
    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        wallets_manager: "WalletsManager",
        my_proof_of_burn_list_service: "MyProofOfBurnListService",
        dao_state_service: "DaoStateService",
    ):
        self._bsq_wallet_service = bsq_wallet_service
        self._btc_wallet_service = btc_wallet_service
        self._wallets_manager = wallets_manager
        self._my_proof_of_burn_list_service = my_proof_of_burn_list_service
        self._dao_state_service = dao_state_service

        self.update_flag = SimpleProperty(0)
        self.proof_of_burn_tx_list: list["Tx"] = []

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self._dao_state_service.add_dao_state_listener(self)

    def start(self):
        pass

    def _update_list(self):
        self.proof_of_burn_tx_list.clear()
        self.proof_of_burn_tx_list.extend(self._get_all_proof_of_burn_txs())
        self.update_flag.set(self.update_flag.get() + 1)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self._update_list()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def burn(self, pre_image_as_string: str, amount: int) -> "Transaction":
        try:
            # We create a prepared Bsq Tx for the burn amount
            prepared_burn_fee_tx = (
                self._bsq_wallet_service.get_prepared_proof_of_burn_tx(amount)
            )
            hash = self._get_hash_from_pre_image(pre_image_as_string)
            op_return_data = ProofOfBurnConsensus.get_op_return_data(hash)
            # We add the BTC inputs for the miner fee.
            tx_with_btc_fee = self._btc_wallet_service.complete_prepared_burn_bsq_tx(
                prepared_burn_fee_tx, op_return_data
            )
            # We sign the BSQ inputs of the final tx.
            transaction = self._bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
                tx_with_btc_fee
            )
            logger.info(f"Proof of burn tx: {transaction}")
            return transaction
        except Exception as e:
            raise TxException(e)

    def publish_transaction(
        self,
        transaction: "Transaction",
        pre_image_as_string: str,
        result_handler: "ResultHandler",
        error_message_handler: "ErrorMessageHandler",
    ):
        class Callback(TxBroadcasterCallback):
            def on_success(self, tx: "Transaction"):
                logger.info(
                    f"Proof of burn tx has been published. TxId={tx.get_tx_id()}"
                )
                result_handler()

            def on_failure(self, exception: Exception):
                error_message_handler(str(exception))

        self._wallets_manager.publish_and_commit_bsq_tx(
            transaction,
            TxType.PROOF_OF_BURN,
            Callback(),
        )

        my_proof_of_burn = MyProofOfBurn(transaction.get_tx_id(), pre_image_as_string)
        self._my_proof_of_burn_list_service.add_my_proof_of_burn(my_proof_of_burn)

    def get_hash_from_op_return_data(self, tx: "Tx") -> bytes:
        return ProofOfBurnConsensus.get_hash_from_op_return_data(
            tx.last_tx_output.op_return_data
        )

    def get_hash_as_string(self, pre_image_as_string: str) -> str:
        return bytes_as_hex_string(self._get_hash_from_pre_image(pre_image_as_string))

    def get_tx(self, tx_id: str) -> Optional["Tx"]:
        return self._dao_state_service.get_tx(tx_id)

    # Of connected output of first input. Used for signing and verification.
    # Proofs ownership of the proof of burn tx.
    def get_pub_key(self, tx_id: str) -> bytes:
        tx = self._dao_state_service.get_tx(tx_id)
        if tx and tx.tx_inputs and tx.tx_inputs[0].pub_key:
            return bytes.fromhex(tx.tx_inputs[0].pub_key)
        return bytes()

    def sign(self, proof_of_burn_tx_id: str, message: str) -> Optional[str]:
        pub_key = self.get_pub_key(proof_of_burn_tx_id)
        key = self._bsq_wallet_service.find_key_from_pub_key(pub_key)
        if key is None:
            return None

        try:
            signature_base64 = key.sign_message(
                message, self._bsq_wallet_service.password
            )
            return signature_base64
        except Exception as e:
            logger.error(str(e), exc_info=e)
            return None

    def verify(self, message: str, pub_key: str, signature_base64: str) -> bool:
        # TODO: check if works correctly
        try:
            return Encryption.verify_ec_message_is_from_pubkey(
                message, signature_base64, bytes.fromhex(pub_key)
            )
        except Exception as e:
            logger.error(str(e), exc_info=e)
            return False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_all_proof_of_burn_txs(self) -> list["Tx"]:
        return sorted(
            filter(
                lambda x: x is not None,
                (
                    self._dao_state_service.get_tx(tx_output.tx_id)
                    for tx_output in self._dao_state_service.get_proof_of_burn_op_return_tx_outputs()
                ),
            ),
            key=lambda tx: tx.time,
            reverse=True,
        )

    def _get_hash_from_pre_image(self, pre_image_as_string: str) -> bytes:
        pre_image = pre_image_as_string.encode("utf-8")
        return ProofOfBurnConsensus.get_hash(pre_image)

    def _get_amount(self, tx: "Tx") -> int:
        return tx.burnt_fee
