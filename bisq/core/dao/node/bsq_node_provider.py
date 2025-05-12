from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING

from bisq.core.dao.node.full.full_node import FullNode
from bisq.core.dao.node.lite.lite_node import LiteNode


if TYPE_CHECKING:
    from bisq.shared.preferences.preferences import Preferences
    from bisq.core.dao.node.bsq_node import BsqNode

class BsqNodeProvider:

    def __init__(
        self,
        bsq_lite_node: "LiteNode",
        bsq_full_node: "FullNode",
        preferences: "Preferences",
    ):
        self.logger = get_ctx_logger(__name__)
        rpc_data_set = (
            preferences.get_rpc_user()
            and preferences.get_rpc_pw()
            and preferences.get_block_notify_port() > 0
        )
        dao_full_node = preferences.is_dao_full_node()
        if dao_full_node and not rpc_data_set:
            self.logger.warning(
                "dao_full_node is set in preferences but RPC user and pw are missing. We reset dao_full_node in preferences to false."
            )
            preferences.set_dao_full_node(False)

        should_use_full_node = dao_full_node and rpc_data_set

        if should_use_full_node:
            self.logger.error(
                "Using bsq full node is not supported yet. falling back to lite node"
            )
            # TODO
            # self.bsq_node = bsq_full_node
            self.bsq_node = bsq_lite_node
        else:
            self.bsq_node = bsq_lite_node
