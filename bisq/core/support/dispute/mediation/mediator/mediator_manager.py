from typing import TYPE_CHECKING

from bisq.core.support.dispute.mediation.mediator.mediator import Mediator
from bisq.core.support.dispute.agent.dispute_agent_manager import DisputeAgentManager

if TYPE_CHECKING:
    from bisq.core.user.user import User
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.support.dispute.mediation.mediator.mediator_service import MediatorService
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry


class MediatorManager(DisputeAgentManager[Mediator]):
    def __init__(self, key_ring: "KeyRing", mediator_service: "MediatorService", user: "User", filter_manager: "FilterManager", use_dev_privilege_keys: bool):
        super().__init__(key_ring, mediator_service, user, filter_manager, use_dev_privilege_keys)

    # TODO: Keep this updated with java impl
    def get_pub_key_list(self):
        return [
            "03be5471ff9090d322110d87912eefe89871784b1754d0707fdb917be5d88d3809",
            "023736953a5a6638db71d7f78edc38cea0e42143c3b184ee67f331dafdc2c59efa",
            "03d82260038253f7367012a4fc0c52dac74cfc67ac9cfbc3c3ad8fca746d8e5fc6",
            "02dac85f726121ef333d425bc8e13173b5b365a6444176306e6a0a9e76ae1073bd",
            "0342a5b37c8f843c3302e930d0197cdd8948a6f76747c05e138a6671a6a4caf739",
            "027afa67c920867a70dfad77db6c6f74051f5af8bf56a1ad479f0bc4005df92325",
            "03505f44f1893b64a457f8883afdd60774d7f4def6f82bb6b60be83a4b5b85cf82",
            "0277d2d505d28ad67a03b001ef66f0eaaf1184fa87ebeaa937703cec7073cb2e8f",
            "027cb3e9a56a438714e2144e2f75db7293ad967f12d5c29b17623efbd35ddbceb0",
            "03be5471ff9090d322110d87912eefe89871784b1754d0707fdb917be5d88d3809",
            "03756937d33d028eea274a3154775b2bffd076ffcc4a23fe0f9080f8b7fa0dab5b",
            "03d8359823a91736cb7aecfaf756872daf258084133c9dd25b96ab3643707c38ca",
            "03589ed6ded1a1aa92d6ad38bead13e4ad8ba24c60ca6ed8a8efc6e154e3f60add",
            "0356965753f77a9c0e33ca7cc47fd43ce7f99b60334308ad3c11eed3665de79a78",
            "031112eb033ebacb635754a2b7163c68270c9171c40f271e70e37b22a2590d3c18"
        ]

    def is_expected_instance(self, data: "ProtectedStorageEntry") -> bool:
        return isinstance(data.protected_storage_payload, Mediator)

    def add_accepted_dispute_agent_to_user(self, dispute_agent: "Mediator"):
        self.user.add_accepted_mediator(dispute_agent)

    def remove_accepted_dispute_agent_from_user(self, data: "ProtectedStorageEntry"):
        self.user.remove_accepted_mediator(data.protected_storage_payload)

    def get_accepted_dispute_agents_from_user(self):
        return self.user.accepted_mediators

    def clear_accepted_dispute_agents_at_user(self):
        self.user.clear_accepted_mediators()

    def get_registered_dispute_agent_from_user(self):
        return self.user.registered_mediator

    def set_registered_dispute_agent_at_user(self, dispute_agent: "Mediator"):
        self.user.set_registered_mediator(dispute_agent)

