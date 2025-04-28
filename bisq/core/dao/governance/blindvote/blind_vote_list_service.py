from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from bisq.core.network.p2p.persistence.append_only_data_store_listener import (
    AppendOnlyDataStoreListener,
)

from utils.data import ObservableList
from bisq.core.dao.governance.blindvote.storage.blind_vote_payload import (
    BlindVotePayload,
)

if TYPE_CHECKING:
    from bisq.core.dao.governance.blindvote.storage.blind_vote_storage_service import (
        BlindVoteStorageService,
    )
    from bisq.core.dao.governance.blindvote.blind_vote_validator import (
        BlindVoteValidator,
    )
    from bisq.core.network.p2p.persistence.append_only_data_store_service import (
        AppendOnlyDataStoreService,
    )
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import (
        PersistableNetworkPayload,
    )


class BlindVoteListService(
    AppendOnlyDataStoreListener, DaoStateListener, DaoSetupService
):
    """Listens for new BlindVotePayload and adds it to appendOnlyStoreList."""

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        p2p_service: "P2PService",
        period_service: "PeriodService",
        blind_vote_storage_service: "BlindVoteStorageService",
        append_only_data_store_service: "AppendOnlyDataStoreService",
        blind_vote_validator: "BlindVoteValidator",
    ):
        self.logger = get_ctx_logger(__name__)
        self.dao_state_service = dao_state_service
        self.p2p_service = p2p_service
        self.period_service = period_service
        self.blind_vote_storage_service = blind_vote_storage_service
        self.blind_vote_validator = blind_vote_validator

        self.blind_vote_payloads = ObservableList["BlindVotePayload"]()

        append_only_data_store_service.add_service(blind_vote_storage_service)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        self.dao_state_service.add_dao_state_listener(self)

    def start(self):
        self._fill_list_from_append_only_data_store()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_new_block_height(self, block_height: int):
        # We only add blindVotes to blindVoteStorageService if we are not in the vote reveal phase.
        self.blind_vote_storage_service.not_in_vote_reveal_phase = (
            self._not_in_vote_reveal_phase(block_height)
        )

    def on_parse_block_chain_complete(self):
        self._fill_list_from_append_only_data_store()

        # We set the listener after parsing is complete to be sure we have a consistent state for the phase check.
        self.p2p_service.p2p_data_storage.add_append_only_data_store_listener(
            self
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // AppendOnlyDataStoreListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_added(self, payload: "PersistableNetworkPayload"):
        self._on_append_only_data_added(payload, True)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_blind_votes_in_phase_and_cycle(self):
        return [
            payload.blind_vote
            for payload in self.blind_vote_payloads
            if self.blind_vote_validator.is_tx_in_phase_and_cycle(payload.blind_vote)
        ]

    def get_confirmed_blind_votes(self):
        return [
            payload.blind_vote
            for payload in self.blind_vote_payloads
            if self.blind_vote_validator.are_data_fields_valid_and_tx_confirmed(
                payload.blind_vote
            )
        ]

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _fill_list_from_append_only_data_store(self):
        for payload in self.blind_vote_storage_service.get_map().values():
            self._on_append_only_data_added(payload, False)

    def _on_append_only_data_added(
        self,
        persistable_network_payload: "PersistableNetworkPayload",
        from_broadcast_message: bool,
    ):
        if isinstance(persistable_network_payload, BlindVotePayload):
            blind_vote_payload = persistable_network_payload
            if blind_vote_payload not in self.blind_vote_payloads:
                blind_vote = blind_vote_payload.blind_vote
                tx_id = blind_vote.tx_id

                if self.blind_vote_validator.are_data_fields_valid(blind_vote):
                    if from_broadcast_message:
                        if self._not_in_vote_reveal_phase(
                            self.dao_state_service.chain_height
                        ):
                            # We received the payload outside the vote reveal phase and add the payload.
                            # If we would accept it during the vote reveal phase we would be vulnerable to a late
                            # publishing attack where the attacker tries to pollute the data view of the voters and
                            # render the whole voting cycle invalid if the majority hash is not at least 80% of the
                            # vote stake.
                            self.blind_vote_payloads.append(blind_vote_payload)
                    else:
                        # In case we received the data from the seed node at startup we cannot apply the phase check as
                        # even in the vote reveal phase we want to receive missed blind votes.
                        self.blind_vote_payloads.append(blind_vote_payload)
                else:
                    self.logger.warning(
                        f"We received an invalid blindVotePayload. blindVoteTxId={tx_id}"
                    )

    def _not_in_vote_reveal_phase(self, block_height: int) -> bool:
        return not self.period_service.is_in_phase(
            block_height, DaoPhase.Phase.VOTE_REVEAL
        )
