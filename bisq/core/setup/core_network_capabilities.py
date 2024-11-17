from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability
from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)

class CoreNetworkCapabilities:

    @staticmethod
    def set_supported_capabilities():
        Capabilities.app.add_all(
            [
                Capability.ACK_MSG,
                Capability.BUNDLE_OF_ENVELOPES,
                Capability.MEDIATION,
                Capability.DAO_STATE, # mandatory capability but we ignore it later
                Capability.SIGNED_ACCOUNT_AGE_WITNESS,
                Capability.REFUND_AGENT,
                Capability.NO_ADDRESS_PRE_FIX,
            ]
        )
        logger.info(Capabilities.app.pretty_print())
