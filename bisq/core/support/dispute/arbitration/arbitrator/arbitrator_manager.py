from typing import TYPE_CHECKING

from bisq.core.support.dispute.arbitration.arbitrator.arbitrator import Arbitrator
from bisq.core.support.dispute.agent.dispute_agent_manager import DisputeAgentManager

if TYPE_CHECKING:
    from bisq.core.user.user import User
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_service import ArbitratorService
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry


class ArbitratorManager(DisputeAgentManager[Arbitrator]):
    def __init__(self, key_ring: "KeyRing", arbitrator_service: "ArbitratorService", user: "User", filter_manager: "FilterManager", use_dev_privilege_keys: bool):
        super().__init__(key_ring, arbitrator_service, user, filter_manager, use_dev_privilege_keys)

    # TODO: Keep this updated with java impl
    def get_pub_key_list(self):
        return [
            "0365c6af94681dbee69de1851f98d4684063bf5c2d64b1c73ed5d90434f375a054",
            "031c502a60f9dbdb5ae5e438a79819e4e1f417211dd537ac12c9bc23246534c4bd",
            "02c1e5a242387b6d5319ce27246cea6edaaf51c3550591b528d2578a4753c56c2c",
            "025c319faf7067d9299590dd6c97fe7e56cd4dac61205ccee1cd1fc390142390a2",
            "038f6e24c2bfe5d51d0a290f20a9a657c270b94ef2b9c12cd15ca3725fa798fc55",
            "0255256ff7fb615278c4544a9bbd3f5298b903b8a011cd7889be19b6b1c45cbefe",
            "024a3a37289f08c910fbd925ebc72b946f33feaeff451a4738ee82037b4cda2e95",
            "02a88b75e9f0f8afba1467ab26799dcc38fd7a6468fb2795444b425eb43e2c10bd",
            "02349a51512c1c04c67118386f4d27d768c5195a83247c150a4b722d161722ba81",
            "03f718a2e0dc672c7cdec0113e72c3322efc70412bb95870750d25c32cd98de17d",
            "028ff47ee2c56e66313928975c58fa4f1b19a0f81f3a96c4e9c9c3c6768075509e",
            "02b517c0cbc3a49548f448ddf004ed695c5a1c52ec110be1bfd65fa0ca0761c94b",
            "03df837a3a0f3d858e82f3356b71d1285327f101f7c10b404abed2abc1c94e7169",
            "0203a90fb2ab698e524a5286f317a183a84327b8f8c3f7fa4a98fec9e1cefd6b72",
            "023c99cc073b851c892d8c43329ca3beb5d2213ee87111af49884e3ce66cbd5ba5"
        ]

    def is_expected_instance(self, data: "ProtectedStorageEntry") -> bool:
        return isinstance(data.protected_storage_payload, Arbitrator)

    def add_accepted_dispute_agent_to_user(self, dispute_agent: "Arbitrator"):
        self.user.add_accepted_arbitrator(dispute_agent)

    def remove_accepted_dispute_agent_from_user(self, data: "ProtectedStorageEntry"):
        self.user.remove_accepted_arbitrator(data.protected_storage_payload)

    def get_accepted_dispute_agents_from_user(self):
        return self.user.accepted_arbitrators

    def clear_accepted_dispute_agents_at_user(self):
        self.user.clear_accepted_arbitrators()

    def get_registered_dispute_agent_from_user(self):
        return self.user.registered_arbitrator

    def set_registered_dispute_agent_at_user(self, dispute_agent: "Arbitrator"):
        self.user.set_registered_arbitrator(dispute_agent)

