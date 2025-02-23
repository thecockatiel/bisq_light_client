from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.node.bsq_node import BsqNode

logger = get_logger(__name__)


# TODO: not going to implement for now
class FullNode(BsqNode):
    """
    Main class for a full node which have Bitcoin Core with rpc running and does the blockchain lookup itself.
    It also provides the BSQ transactions to lite nodes on request and broadcasts new BSQ blocks.

    JAVA TODO request p2p network data again after parsing is complete to be sure that in case we missed data during parsing
    we get it added.
    """

    def __init__(self):
        pass

    def start(self):
        pass

    def start_parse_blocks(self):
        pass
