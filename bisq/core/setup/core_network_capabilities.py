from typing import TYPE_CHECKING
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bisq.common.config.config import Config

logger = get_logger(__name__)


class CoreNetworkCapabilities:

    @staticmethod
    def set_supported_capabilities(config: "Config"):
        Capabilities.app.add_all(
            [
                # Capability.TRADE_STATISTICS,
                # Capability.TRADE_STATISTICS_2,
                Capability.ACCOUNT_AGE_WITNESS,
                Capability.ACK_MSG,
                Capability.PROPOSAL,
                Capability.BLIND_VOTE,
                Capability.DAO_STATE, # mandatory capability
                Capability.BUNDLE_OF_ENVELOPES,
                Capability.MEDIATION,
                Capability.SIGNED_ACCOUNT_AGE_WITNESS,
                Capability.REFUND_AGENT,
                # Capability.TRADE_STATISTICS_HASH_UPDATE,
                Capability.NO_ADDRESS_PRE_FIX,
                # Capability.TRADE_STATISTICS_3,
                Capability.BSQ_SWAP_OFFER
            ]
        )

        CoreNetworkCapabilities.maybe_apply_dao_full_mode(config)

        logger.info(Capabilities.app.pretty_print())

    @staticmethod
    def maybe_apply_dao_full_mode(config: "Config"):
        # If we set dao full mode at the preferences view we add the capability there. We read the preferences a
        # bit later than we call that method so we have to add DAO_FULL_NODE Capability at preferences as well to
        # be sure it is set in both cases.
        if config.full_dao_node:
            # Capabilities.app.add_all([Capability.DAO_FULL_NODE])
            # TODO: uncomment above if full node is implemented
            Capabilities.app.add_all([Capability.RECEIVE_BSQ_BLOCK])
        else:
            # A lite node has the capability to receive bsq blocks. We do not want to send BSQ blocks to full nodes
            # as they ignore them anyway.
            Capabilities.app.add_all([Capability.RECEIVE_BSQ_BLOCK])
