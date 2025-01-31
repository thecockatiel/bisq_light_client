from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.core.api.exception.not_available_exception import NotAvailableException
from bisq.core.exceptions.unsupported_operation_exception import (
    UnsupportedOperationException,
)
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.support.dispute.mediation.mediator.mediator import Mediator
from bisq.core.support.refund.refundagent.refund_agent import RefundAgent
from bisq.core.support.support_type import SupportType
from bisq.common.crypto.encryption import ECPubkey
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.common.config.config import Config
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.support.dispute.mediation.mediator.mediator_manager import (
        MediatorManager,
    )
    from bisq.core.support.refund.refundagent.refund_agent_manager import (
        RefundAgentManager,
    )


class CoreDisputeAgentsService:
    def __init__(
        self,
        config: "Config",
        key_ring: "KeyRing",
        mediator_manager: "MediatorManager",
        refund_agent_manager: "RefundAgentManager",
        p2p_service: "P2PService",
    ):
        self.config = config
        self.key_ring = key_ring
        self.mediator_manager = mediator_manager
        self.refund_agent_manager = refund_agent_manager
        self.p2p_service = p2p_service
        self.node_address = NodeAddress("127.0.0.1", config.node_port)
        self.language_codes = ["de", "en", "es", "fr"]

    def register_dispute_agent(self, dispute_agent_type: str, registration_key: str):
        if not self.p2p_service.is_bootstrapped:
            raise NotAvailableException("p2p service is not bootstrapped yet")

        if (
            self.config.base_currency_network.is_mainnet()
            or self.config.base_currency_network.is_dao_betanet()
            or not self.config.use_localhost_for_p2p
        ):
            raise UnsupportedOperationException(
                "dispute agents must be registered in a Bisq UI"
            )

        if registration_key != DevEnv.DEV_PRIVILEGE_PRIV_KEY:
            raise ValueError("invalid registration key")

        support_type = self._get_support_type(dispute_agent_type)

        if support_type is None:
            raise ValueError(f"unknown dispute agent type '{dispute_agent_type}'")

        if support_type == SupportType.ARBITRATION:
            raise UnsupportedOperationException(
                "arbitrators must be registered in a Bisq UI"
            )
        elif support_type == SupportType.MEDIATION:
            ec_key = self.mediator_manager.get_registration_key(registration_key)
            assert ec_key is not None
            signature = self.mediator_manager.sign_storage_signature_pub_key(ec_key)
            self._register_mediator(
                self.node_address, self.language_codes, ec_key, signature
            )
        elif support_type == SupportType.REFUND:
            ec_key = self.refund_agent_manager.get_registration_key(registration_key)
            assert ec_key is not None
            signature = self.refund_agent_manager.sign_storage_signature_pub_key(ec_key)
            self._register_refund_agent(
                self.node_address, self.language_codes, ec_key, signature
            )
        elif support_type == SupportType.TRADE:
            raise UnsupportedOperationException(
                "trade agent registration not supported"
            )

    def _register_mediator(
        self,
        node_address: "NodeAddress",
        language_codes: list[str],
        ec_key: "ECPubkey",
        signature: str,
    ):
        mediator = Mediator(
            node_address,
            self.key_ring.pub_key_ring,
            language_codes,
            get_time_ms(),
            ec_key.get_public_key_bytes(),
            signature,
            None,
            None,
            None,
        )
        self.mediator_manager.add_dispute_agent(
            mediator, lambda: None, lambda error_message: None
        )
        if not self.mediator_manager.get_dispute_agent_by_node_address(
            self.node_address
        ):
            raise RuntimeError("could not register mediator")

    def _register_refund_agent(
        self,
        node_address: "NodeAddress",
        language_codes: list[str],
        ec_key: "ECPubkey",
        signature: str,
    ):
        refund_agent = RefundAgent(
            node_address,
            self.key_ring.pub_key_ring,
            language_codes,
            get_time_ms(),
            ec_key.get_public_key_bytes(),
            signature,
            None,
            None,
            None,
        )
        self.refund_agent_manager.add_dispute_agent(
            refund_agent, lambda: None, lambda error_message: None
        )
        if not self.refund_agent_manager.get_dispute_agent_by_node_address(
            node_address
        ):
            raise RuntimeError("could not register refund agent")

    def _get_support_type(self, dispute_agent_type: str) -> Optional[SupportType]:
        dispute_agent_type = dispute_agent_type.lower()
        if dispute_agent_type == "arbitrator":
            return SupportType.ARBITRATION
        elif dispute_agent_type == "mediator":
            return SupportType.MEDIATION
        elif dispute_agent_type in ["refundagent", "refund_agent"]:
            return SupportType.REFUND
        elif dispute_agent_type in ["tradeagent", "trade_agent"]:
            return SupportType.TRADE
        else:
            return None
