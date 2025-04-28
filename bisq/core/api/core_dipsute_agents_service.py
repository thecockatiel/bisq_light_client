from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.core.api.exception.not_available_exception import NotAvailableException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
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
    from bisq.core.user.user_context import UserContext


class CoreDisputeAgentsService:
    def __init__(
        self,
        config: "Config",
    ):
        self._config = config
        self._node_address = NodeAddress("127.0.0.1", config.node_port)
        self._language_codes = ["de", "en", "es", "fr"]

    def register_dispute_agent(
        self,
        user_context: "UserContext",
        dispute_agent_type: str,
        registration_key: str,
    ):
        p2p_service = user_context.global_container.p2p_service
        mediator_manager = user_context.global_container.mediator_manager
        refund_agent_manager = user_context.global_container.refund_agent_manager

        if not p2p_service.is_bootstrapped:
            raise NotAvailableException("p2p service is not bootstrapped yet")

        if (
            self._config.base_currency_network.is_mainnet()
            or self._config.base_currency_network.is_dao_betanet()
            or not self._config.use_localhost_for_p2p
        ):
            raise UnsupportedOperationException(
                "dispute agents must be registered in a Bisq UI"
            )

        if registration_key != DevEnv.DEV_PRIVILEGE_PRIV_KEY:
            raise IllegalArgumentException("invalid registration key")

        support_type = self._get_support_type(dispute_agent_type)

        if support_type is None:
            raise IllegalArgumentException(
                f"unknown dispute agent type '{dispute_agent_type}'"
            )

        if support_type == SupportType.ARBITRATION:
            raise UnsupportedOperationException(
                "arbitrators must be registered in a Bisq UI"
            )
        elif support_type == SupportType.MEDIATION:
            ec_key = mediator_manager.get_registration_key(registration_key)
            assert ec_key is not None
            signature = mediator_manager.sign_storage_signature_pub_key(ec_key)
            self._register_mediator(
                user_context,
                self._node_address,
                self._language_codes,
                ec_key,
                signature,
            )
        elif support_type == SupportType.REFUND:
            ec_key = refund_agent_manager.get_registration_key(registration_key)
            assert ec_key is not None
            signature = refund_agent_manager.sign_storage_signature_pub_key(ec_key)
            self._register_refund_agent(
                user_context,
                self._node_address,
                self._language_codes,
                ec_key,
                signature,
            )
        elif support_type == SupportType.TRADE:
            raise UnsupportedOperationException(
                "trade agent registration not supported"
            )

    def _register_mediator(
        self,
        user_context: "UserContext",
        node_address: "NodeAddress",
        language_codes: list[str],
        ec_key: "ECPubkey",
        signature: str,
    ):
        key_ring = user_context.global_container.key_ring
        mediator_manager = user_context.global_container.mediator_manager
        mediator = Mediator(
            node_address,
            key_ring.pub_key_ring,
            language_codes,
            get_time_ms(),
            ec_key.get_public_key_bytes(),
            signature,
            None,
            None,
            None,
        )
        mediator_manager.add_dispute_agent(
            mediator, lambda: None, lambda error_message: None
        )
        if not mediator_manager.get_dispute_agent_by_node_address(self._node_address):
            raise RuntimeError("could not register mediator")

    def _register_refund_agent(
        self,
        user_context: "UserContext",
        node_address: "NodeAddress",
        language_codes: list[str],
        ec_key: "ECPubkey",
        signature: str,
    ):
        key_ring = user_context.global_container.key_ring
        refund_agent_manager = user_context.global_container.refund_agent_manager
        refund_agent = RefundAgent(
            node_address,
            key_ring.pub_key_ring,
            language_codes,
            get_time_ms(),
            ec_key.get_public_key_bytes(),
            signature,
            None,
            None,
            None,
        )
        refund_agent_manager.add_dispute_agent(
            refund_agent, lambda: None, lambda error_message: None
        )
        if not refund_agent_manager.get_dispute_agent_by_node_address(node_address):
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
