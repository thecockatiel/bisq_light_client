from typing import TYPE_CHECKING

from bisq.core.support.refund.refundagent.refund_agent import RefundAgent
from bisq.core.support.dispute.agent.dispute_agent_manager import DisputeAgentManager

if TYPE_CHECKING:
    from bisq.core.user.user import User
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.support.refund.refundagent.refund_agent_service import RefundAgentService
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry


class RefundAgentManager(DisputeAgentManager[RefundAgent]):
    def __init__(self, key_ring: "KeyRing", refund_agent_service: "RefundAgentService", user: "User", filter_manager: "FilterManager", use_dev_privilege_keys: bool):
        super().__init__(key_ring, refund_agent_service, user, filter_manager, use_dev_privilege_keys)

    # TODO: Keep this updated with java impl
    def get_pub_key_list(self):
        return [
            "02a25798e256b800d7ea71c31098ac9a47cb20892176afdfeb051f5ded382d44af",
            "0360455d3cffe00ef73cc1284c84eedacc8c5c3374c43f4aac8ffb95f5130b9ef5",
            "03b0513afbb531bc4551b379eba027feddd33c92b5990fd477b0fa6eff90a5b7db",
            "03533fd75fda29c351298e50b8ea696656dcb8ce4e263d10618c6901a50450bf0e",
            "028124436482aa4c61a4bc4097d60c80b09f4285413be3b023a37a0164cbd5d818",
            "0384fcf883116d8e9469720ed7808cc4141f6dc6a5ed23d76dd48f2f5f255590d7",
            "029bd318ecee4e212ff06a4396770d600d72e9e0c6532142a428bdb401491e9721",
            "02e375b4b24d0a858953f7f94666667554d41f78000b9c8a301294223688b29011",
            "0232c088ae7c070de89d2b6c8d485b34bf0e3b2a964a2c6622f39ca501260c23f7",
            "033e047f74f2aa1ce41e8c85731f97ab83d448d65dc8518ab3df4474a5d53a3d19",
            "02f52a8cf373c8cbddb318e523b7f111168bf753fdfb6f8aa81f88c950ede3a5ce",
            "039784029922c54bcd0f0e7f14530f586053a5f4e596e86b3474cd7404657088ae",
            "037969f9d5ab2cc609104c6e61323df55428f8f108c11aab7c7b5f953081d39304",
            "031bd37475b8c5615ac46d6816e791c59d806d72a0bc6739ae94e5fe4545c7f8a6",
            "021bb92c636feacf5b082313eb071a63dfcd26501a48b3cd248e35438e5afb7daf"
        ]

    def is_expected_instance(self, data: "ProtectedStorageEntry") -> bool:
        return isinstance(data.protected_storage_payload, RefundAgent)

    def add_accepted_dispute_agent_to_user(self, dispute_agent: "RefundAgent"):
        self.user.add_accepted_refund_agent(dispute_agent)

    def remove_accepted_dispute_agent_from_user(self, data: "ProtectedStorageEntry"):
        self.user.remove_accepted_refund_agent(data.protected_storage_payload)

    def get_accepted_dispute_agents_from_user(self):
        return self.user.accepted_refund_agents

    def clear_accepted_dispute_agents_at_user(self):
        self.user.clear_accepted_refund_agents()

    def get_registered_dispute_agent_from_user(self):
        return self.user.registered_refund_agent

    def set_registered_dispute_agent_at_user(self, dispute_agent: "RefundAgent"):
        self.user.set_registered_refund_agent(dispute_agent)

