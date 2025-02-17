from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from bisq.common.setup.log_setup import get_logger
from bisq.common.version import Version
from bisq.core.btc.exceptions.transaction_verification_exception import (
    TransactionVerificationException,
)
from bisq.core.btc.exceptions.wallet_exception import WalletException
from bisq.core.dao.governance.proposal.issuance_proposal import IssuanceProposal
from bisq.core.dao.governance.proposal.proposal_consensus import ProposalConsensus
from bisq.core.dao.governance.proposal.proposal_with_transaction import (
    ProposalWithTransaction,
)
from bisq.core.dao.governance.proposal.tx_exception import TxException
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.dao.governance.proposal.proposal_validator import ProposalValidator
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.proposal import Proposal

_R = TypeVar("_R", bound="Proposal")

logger = get_logger(__name__)


class BaseProposalFactory(Generic[_R], ABC):
    """
    Base class for proposalFactory classes. Provides creation of a transaction. Proposal creation is delegated to
    concrete classes.
    """

    def __init__(
        self,
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_service: "DaoStateService",
        proposal_validator: "ProposalValidator",
    ):
        self._bsq_wallet_service = bsq_wallet_service
        self._btc_wallet_service = btc_wallet_service
        self._dao_state_service = dao_state_service
        self._proposal_validator = proposal_validator

        self.name: Optional[str] = None
        self.link: Optional[str] = None

    def create_proposal_with_transaction(
        self, name: str, link: str
    ) -> "ProposalWithTransaction":
        self.name = name
        self.link = link
        # As we don't know the txId yet we create a temp proposal with txId set to an empty string.
        proposal = self.create_proposal_without_tx_id()
        self._proposal_validator.validate_data_fields(proposal)
        transaction = self.create_transaction(proposal)
        proposal_with_tx_id = proposal.clone_proposal_and_add_tx_id(
            transaction.get_tx_id()
        )
        return ProposalWithTransaction(proposal_with_tx_id, transaction)

    @abstractmethod
    def create_proposal_without_tx_id(self) -> _R:
        pass

    # We have txId set to null in proposal as we cannot know it before the tx is created.
    # Once the tx is known we will create a new object including the txId.
    # The hashOfPayload used in the opReturnData is created with the txId set to null.
    def create_transaction(self, proposal: _R) -> "Transaction":
        try:
            fee = ProposalConsensus.get_fee(
                self._dao_state_service, self._dao_state_service.chain_height
            )
            # We create a prepared Bsq Tx for the proposal fee.
            prepared_burn_fee_tx = (
                self._bsq_wallet_service.get_prepared_issuance_tx(fee)
                if isinstance(proposal, IssuanceProposal)
                else self._bsq_wallet_service.get_prepared_proposal_tx(fee)
            )

            # payload does not have txId at that moment
            hash_of_payload = ProposalConsensus.get_hash_of_payload(proposal)
            op_return_data = self.get_op_return_data(hash_of_payload)

            # We add the BTC inputs for the miner fee.
            tx_with_btc_fee = self.complete_tx(prepared_burn_fee_tx, op_return_data)

            # We sign the BSQ inputs of the final tx.
            transaction = self._bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
                tx_with_btc_fee
            )
            logger.info(f"Proposal tx: {transaction}")
            return transaction
        except (WalletException, TransactionVerificationException) as e:
            raise TxException(e)

    def get_op_return_data(self, hash_of_payload: bytes) -> bytes:
        return ProposalConsensus.get_op_return_data(
            hash_of_payload, OpReturnType.PROPOSAL.type, Version.PROPOSAL
        )

    def complete_tx(
        self,
        prepared_burn_fee_tx: "Transaction",
        op_return_data: bytes,
    ) -> "Transaction":
        return self._btc_wallet_service.complete_prepared_burn_bsq_tx(
            prepared_burn_fee_tx, op_return_data
        )
