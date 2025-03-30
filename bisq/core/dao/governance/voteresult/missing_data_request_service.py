from datetime import timedelta
import random
from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.proposal.proposal_service import ProposalService
from utils.data import ObservableList

if TYPE_CHECKING:
    from bisq.core.dao.governance.blindvote.storage.blind_vote_payload import (
        BlindVotePayload,
    )
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
        BlindVoteListService,
    )
    from bisq.core.dao.governance.blindvote.network.republish_governance_data_handler import (
        RepublishGovernanceDataHandler,
    )
    from bisq.core.dao.governance.proposal.storage.appendonly.proposal_payload import (
        ProposalPayload,
    )


logger = get_logger(__name__)


class MissingDataRequestService(DaoSetupService):

    def __init__(
        self,
        republish_governance_data_handler: "RepublishGovernanceDataHandler",
        blind_vote_list_service: "BlindVoteListService",
        proposal_service: "ProposalService",
        p2p_service: "P2PService",
    ):
        self._republish_governance_data_handler = republish_governance_data_handler
        self._blind_vote_list_service = blind_vote_list_service
        self._proposal_service = proposal_service
        self._p2p_service = p2p_service
        self._re_republish_all_governance_data_done = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        pass

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_republish_request(self):
        self._republish_governance_data_handler.send_republish_request()

    # Can be triggered with shortcut ctrl+h, cmd+h or alt+h
    def re_republish_all_governance_data(self):
        # We only want to do it once in case we would get flooded with requests.
        if not self._re_republish_all_governance_data_done:
            self._re_republish_all_governance_data_done = True
            proposal_payloads = self._proposal_service.proposal_payloads
            for proposal_payload in proposal_payloads:
                # We want a random delay between 0.1 and 300 sec. depending on the number of items.
                # We send all proposals including those from old cycles.
                delay = max(0.1, min(300, random.randint(0, len(proposal_payloads))))
                UserThread.run_after(
                    lambda p=proposal_payload: self._republish_proposal_payload(p),
                    timedelta(seconds=delay),
                )

            blind_vote_payloads = self._blind_vote_list_service.blind_vote_payloads
            for blind_vote_payload in blind_vote_payloads:
                # We want a random delay between 0.1 and 300 sec. depending on the number of items.
                # We send all blindVotes including those from old cycles.
                delay = max(
                    0.1,
                    min(300, random.randint(0, len(blind_vote_payloads))),
                )
                UserThread.run_after(
                    lambda bvp=blind_vote_payload: self._republish_blind_vote_payload(bvp),
                    timedelta(seconds=delay),
                )

    def _republish_proposal_payload(self, proposal_payload: "ProposalPayload"):
        success = self._p2p_service.add_persistable_network_payload(
            proposal_payload, True
        )
        tx_id = proposal_payload.proposal.tx_id
        if success:
            logger.debug(
                f"We received a RepublishGovernanceDataRequest and re-published a proposalPayload to the P2P network as append only data. proposalTxId={tx_id}"
            )
        else:
            logger.error(
                f"Adding of proposalPayload to P2P network failed. proposalTxId={tx_id}"
            )

    def _republish_blind_vote_payload(self, blind_vote_payload: "BlindVotePayload"):
        success = self._p2p_service.add_persistable_network_payload(
            blind_vote_payload, True
        )
        tx_id = blind_vote_payload.blind_vote.tx_id
        if success:
            logger.debug(
                f"We received a RepublishGovernanceDataRequest and re-published a blindVotePayload to the P2P network as append only data. blindVoteTxId={tx_id}"
            )
        else:
            logger.error(
                f"Adding of blindVotePayload to P2P network failed. blindVoteTxId={tx_id}"
            )
